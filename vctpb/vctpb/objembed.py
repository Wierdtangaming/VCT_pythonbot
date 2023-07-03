import discord
from discord.ui import View, Button
from discord.ui.item import ItemCallbackType
from dbinterface import get_mult_from_db, get_condition_db, get_from_db, delete_from_db
from Match import Match
from Bet import Bet
from Tournament import Tournament
from User import User, get_active_users
from convert import ambig_to_obj, id_to_mention, get_user_from_ctx, get_users_hidden_match_bets
from colorinterface import hex_to_tuple
import math
import emoji
from sqlaobjs import Session
from functools import partial


async def show_bets(match, user, interaction, session):
  if match is None: return
  hidden_bets = []
  if user is not None:
    hidden_bets = get_users_hidden_match_bets(user, match.code, session)
  bets = match.bets
  if len(bets) == 0:
    await interaction.response.send_message("No undecided bets.", ephemeral=True)
    return
  embeds = []
  if (embedd := create_bet_list_embedded("Bets:", bets, False, session)) is not None:
    embeds.append(embedd)
  if (hidden_embedd := create_bet_list_embedded("Your Hidden Bets:", hidden_bets, True, session)) is not None:
    embeds.append(hidden_embedd)
  await interaction.response.send_message(embeds=embeds, ephemeral=True)
    
async def show_match(match, interaction, session):
  if (embedd := create_match_embedded(match, f"Match: {match.t1} vs {match.t2}, {match.t1o} / {match.t2o}.", session)) is not None:
    await interaction.response.send_message(embed=embedd, ephemeral=True)
  else:
    await interaction.response.send_message("Match not found. Report the bug.", ephemeral=True)

async def create_edit_bet(interaction, hide, team, match, session, bot):
    from modals import BetEditModal, BetCreateModal
    user = get_from_db("User", interaction.user.id, session)
    if match.date_closed is None:
      if (bet := match.user_bet(interaction.user.id)) != None:
        bet_modal = BetEditModal(int(hide), match, user, bet, session, bot, title="Edit Bet", team=team)
        await interaction.response.send_modal(bet_modal)
      else:
        bet_modal = BetCreateModal(match, user, int(hide), session, title="Create Bet", bot=bot, team=team)
        await interaction.response.send_modal(bet_modal)
    else:
      await interaction.response.send_message("Betting on this match has closed.", ephemeral=True)
      
class MatchView(View): 
  def __init__(self, bot, match):
    self.bot = bot
    super().__init__(timeout=None)
    if match is not None:
      if match.date_closed is not None:
        self.hide_buttons()
      else:
        self.set_buttons(match)
  
  def hide_buttons(self):
    self.remove_item(self.get_item("match_create_bet_t1")) # type: ignore
    self.remove_item(self.get_item("match_create_bet_t2")) # type: ignore
    self.remove_item(self.get_item("match_create_hidden_bet_t1")) # type: ignore
    self.remove_item(self.get_item("match_create_hidden_bet_t2")) # type: ignore
  
  def set_buttons(self, match):
    self.get_item("match_create_bet_t1").label = f"{match.t1} ({match.t1o})" # type: ignore
    self.get_item("match_create_bet_t2").label = f"{match.t2} ({match.t2o})" # type: ignore
    self.get_item("match_create_hidden_bet_t1").label = f"{match.t1} ({match.t1o})" # type: ignore
    self.get_item("match_create_hidden_bet_t2").label = f"{match.t2} ({match.t2o})" # type: ignore
    
    
  async def get_match(self, interaction, session):
    match = None
    fields = interaction.message.embeds[0].fields
    for field in fields[::-1]:
      if field.name == "ID:":
        match_id = field.value
        match = get_from_db("Match", match_id, session)
        break
    if match is None and interaction is not None:
      await interaction.response.send_message("Match not found. Report the bug.", ephemeral=True)
    return match
  
  @discord.ui.button(label='Create/Edit Bet', custom_id="match_create_bet_t1", style=discord.ButtonStyle.green, row=0)
  async def create_bet_t1_callback(self, button, interaction):
    with Session.begin() as session:
      if (match := await self.get_match(interaction, session)) is None: return
      await create_edit_bet(interaction, False, 1, match, session, self.bot)
      
  @discord.ui.button(label='Create/Edit Bet', custom_id="match_create_bet_t2", style=discord.ButtonStyle.green, row=0)
  async def create_bet_t2_callback(self, button, interaction):
    with Session.begin() as session:
      if (match := await self.get_match(interaction, session)) is None: return
      await create_edit_bet(interaction, False, 2, match, session, self.bot)
    
  @discord.ui.button(label='Create/Edit Hidden Bet', custom_id="match_create_hidden_bet_t1", style=discord.ButtonStyle.secondary, row=1)
  async def create_hidden_bet_t1_callback(self, button, interaction):
    with Session.begin() as session:
      if (match := await self.get_match(interaction, session)) is None: return
      await create_edit_bet(interaction, True, 1, match, session, self.bot)
  
  @discord.ui.button(label='Create/Edit Hidden Bet', custom_id="match_create_hidden_bet_t2", style=discord.ButtonStyle.secondary, row=1)
  async def create_hidden_bet_t2_callback(self, button, interaction):
    with Session.begin() as session:
      if (match := await self.get_match(interaction, session)) is None: return
      await create_edit_bet(interaction, True, 2, match, session, self.bot)
      
  # show all bets
  @discord.ui.button(label='Show Bets', custom_id="match_show_bets", style=discord.ButtonStyle.primary, row=2)
  async def show_bets_callback(self, button, interaction):
    with Session.begin() as session:
      if (match := await self.get_match(interaction, session)) is None: return
      user = get_from_db("User", interaction.user.id, session)
      await show_bets(match, user, interaction, session)
    
class BetView(View):
  async def get_bet(self, interaction, session):
    bet = None
    fields = interaction.message.embeds[0].fields
    for field in fields[::-1]:
      if field.name == "ID:":
        bet_id = field.value
        bet = get_from_db("Bet", bet_id, session)
        break
    if bet is None and interaction is not None:
      await interaction.response.send_message("Bet not found. Report the bug.", ephemeral=True)
    return bet
  
  async def get_match(self, interaction, session):
    if (bet := await self.get_bet(interaction, session)) is None: return None
    return bet.match
  
  def __init__(self, bot, bet):
    self.bot = bot
    super().__init__(timeout=None)
    if bet is not None:
      match = bet.match
      if match.date_closed is not None:
        self.remove_item(self.get_item("bet_cancel_bet")) # type: ignore
        self.remove_item(self.get_item("bet_edit_bet")) # type: ignore
  
  @discord.ui.button(label="Edit Bet", custom_id="bet_edit_bet", style=discord.ButtonStyle.green, row=0)
  async def edit_bet_callback(self, button, interaction):
    with Session.begin() as session:
      if (match := await self.get_match(interaction, session)) is None: return
      await create_edit_bet(interaction, -1, -1, match, session, self.bot)
  
  @discord.ui.button(label="Cancel Bet", custom_id="bet_cancel_bet", style=discord.ButtonStyle.danger, row=0)
  async def cancel_bet_callback(self, button, interaction):
    with Session.begin() as session:
      if (bet := await self.get_bet(interaction, session)) is None: return
      match = bet.match
      if (match is None) or (match.date_closed is not None):
        await interaction.response.send_message(content="Match betting has closed, you cannot cancel the bet.", ephemeral=True)
        return
        
      user = bet.user
      if bet.hidden == 0:
        embedd = create_bet_embedded(bet, f"Cancelled Bet: {user.username}, {bet.amount_bet} on {bet.get_team()}.", session)
      else:
        embedd = create_bet_hidden_embedded(bet, f"Cancelled Bet: {user.username}'s Hidden Bet on {bet.t1} vs {bet.t2}", session)
      await interaction.response.send_message(content="", embed=embedd)
      
      await delete_from_db(bet, self.bot, session=session)
  
  @discord.ui.button(label='Show Bets', custom_id="bet_show_bets", style=discord.ButtonStyle.primary, row=1)
  async def show_bets_callback(self, button, interaction):
    with Session.begin() as session:
      if (match := await self.get_match(interaction, session)) is None: return
      user = get_from_db("User", interaction.user.id, session)
      await show_bets(match, user, interaction, session)
  
  @discord.ui.button(label='Show Match', custom_id="bet_show_match", style=discord.ButtonStyle.primary, row=1)
  async def show_match_callback(self, button, interaction):
    with Session.begin() as session:
      if (match := await self.get_match(interaction, session)) is None: return
      await show_match(match, interaction, session)
  
  
class MatchListView(View):
  async def get_match(self, button, interaction, session):
    match = None
    fields = interaction.message.embeds[0].fields
    view = self.from_message(interaction.message)
    label = view.get_item(button.custom_id).label # type: ignore
    for field in fields:
      if label in field.name:
        match_id = field.name.split("ID: ")[-1]
        match = get_from_db("Match", match_id, session)
        break
    if match is None and interaction is not None:
      await interaction.response.send_message("Match not found. Report the bug.", ephemeral=True)
    return match
  
  def __init__(self, bot, matches):
    self.bot = bot
    super().__init__(timeout=None)
    
    if matches is not None:
      i = 0
      for match in matches:
        button = Button(label=f"{match.t1} vs {match.t2}", custom_id=f"match_list_{i}", style=discord.ButtonStyle.primary)
        self.add_item(button)
        button.callback = partial(self.match_list_callback, button)
        i += 1
    else:
      for i in range(0, 25):
        button = Button(label=str(i), custom_id=f"match_list_{i}", style=discord.ButtonStyle.primary, disabled=True)
        self.add_item(button)
        button.callback = partial(self.match_list_callback, button)
  
  async def match_list_callback(self, button, interaction):
    with Session.begin() as session:
      if (match := await self.get_match(button, interaction, session)) is None: return
      await create_edit_bet(interaction, -1, -1, match, session, self.bot)
  
  

def create_match_embedded(match_ambig, title, session=None):
  if session is None:
    with Session.begin() as session:
      return create_match_embedded(match_ambig, title, session)
    
  match = ambig_to_obj(match_ambig, "Match", session)
  if match is None:
    return None
  
  embed = discord.Embed(title=title, color=discord.Color.from_rgb(*hex_to_tuple(match.color_hex)))
  embed.add_field(name="Teams:", value=f"{match.t1} vs {match.t2}", inline=True)
  embed.add_field(name="Odds:", value=str(match.t1o) + " / " + str(match.t2o), inline=True)
  embed.add_field(name="Tournament Name:", value=match.tournament_name, inline=True)
  embed.add_field(name="Odds Source:", value=match.odds_source, inline=True)
  embed.add_field(name="Creator:", value=id_to_mention(match.creator_id), inline=True)
  bet_codes = [bet.code for bet in match.bets]
  bet_str = str(", ".join(bet_codes))
  if bet_str == "":
    bet_str = "None"
  #embed.add_field(name="Bet IDs:", value=bet_str, inline=True)
  #date_formatted = match.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  #embed.add_field(name="Created On:", value=date_formatted, inline=True)
  if match.date_closed is None:
    embed.add_field(name="Betting Open:", value="Yes", inline=True)
  else:
    embed.add_field(name="Betting Open:", value="No", inline=True)

  if int(match.winner) == 0:
    #embed.add_field(name="Winner:", value="None", inline=True)
    pass
  else:
    winner_team = ""
    if int(match.winner) == 1:
      winner_team = match.t1
    else:
      winner_team = match.t2

    embed.add_field(name="Winner:", value=winner_team, inline=True)
    
  embed.add_field(name="ID:", value=match.code, inline=True)
  return embed


def create_match_list_embedded(embed_title, matches_ambig, session=None):
  if session is None:
    with Session.begin() as session:
      return create_match_list_embedded(embed_title, matches_ambig, session)
    
  if len(matches_ambig) > 24:
    embeds = []
    while len(matches_ambig) > 0:
      embeds.append(create_match_list_embedded(embed_title, matches_ambig[:24], session))
      matches_ambig = matches_ambig[24:]
    return embeds
  
  embed = discord.Embed(title=embed_title, color=discord.Color.red())
  if all(isinstance(s, str) for s in matches_ambig):
    matches_ambig = get_mult_from_db("Match", matches_ambig, session)
  for match in matches_ambig:
    embed.add_field(name=f"{match.t1} vs {match.t2}, Odds: {match.t1o} / {match.t2o}, ID: {match.code}", value="", inline=False)
  return embed

async def channel_send_match_list_embedded(channel, embed_title, matches_ambig, session=None):
  if session is None:
    with Session.begin() as session:
      return await channel_send_match_list_embedded(channel, embed_title, matches_ambig, session)
    
  embeds = create_match_list_embedded(embed_title, matches_ambig, session)
  if isinstance(embeds, list):
    for embed in embeds:
      await channel.send(embed=embed)
  else:
    await channel.send(embed=embeds)

async def respond_send_match_list_embedded(ctx, embed_title, matches_ambig, session=None, bot=None):
  if session is None:
    with Session.begin() as session:
      return await channel_send_match_list_embedded(ctx, embed_title, matches_ambig, session)
  embeds = create_match_list_embedded(embed_title, matches_ambig, session)
  if isinstance(embeds, list):
    for i, embedd in enumerate(embeds):
      if i == 0:
        await ctx.respond(embed=embedd, view=MatchListView(bot, matches_ambig))
      else:
        await ctx.interaction.followup.send(embed=embedd)
  else:
    await ctx.respond(embed=embeds, view=MatchListView(bot, matches_ambig))

def create_bet_hidden_embedded(bet_ambig, title, session=None):
  if session is None:
    with Session.begin() as session:
      return create_bet_hidden_embedded(bet_ambig, title, session)
    
  bet = ambig_to_obj(bet_ambig, "Bet", session)
  if bet is None:
    return None
  
  embed = discord.Embed(title=title, color=discord.Color.from_rgb(*hex_to_tuple(bet.color_hex)))
  #when teams done this has to be diff color
  embed.add_field(name="User:", value=id_to_mention(bet.user_id), inline=True)
  embed.add_field(name="Teams:", value=bet.t1 + " vs " + bet.t2, inline=True)

  if int(bet.winner) == 0:
    #embed.add_field(name="Winner:", value="None", inline=True)
    pass
  else:
    winner_team = ""
    if int(bet.winner) == 1:
      winner_team = bet.t1
    else:
      winner_team = bet.t2

    embed.add_field(name="Winner:", value=winner_team, inline=True)

  #date_formatted = bet.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  #embed.add_field(name="Created On:", value=date_formatted, inline=True)
  #embed.add_field(name="Match ID:", value=bet.match_id, inline=True)
  embed.add_field(name="ID:", value=str(bet.code), inline=True)
  return embed


def create_bet_embedded(bet_ambig, title, session=None):
  if session is None:
    with Session.begin() as session:
      return create_bet_embedded(bet_ambig, title, session)
    
  bet = ambig_to_obj(bet_ambig, "Bet", session)
  if bet is None:
    return None
  
  embed = discord.Embed(title=title, color=discord.Color.from_rgb(*hex_to_tuple(bet.color_hex)))
  embed.add_field(name="User:", value=id_to_mention(bet.user_id), inline=True)
  embed.add_field(name="Amount Bet:", value=bet.amount_bet, inline=True)
  (team, payout) = bet.get_team_and_payout(session)

  embed.add_field(name="Bet on:", value=team, inline=True)
  embed.add_field(name="Payout On Win:", value=math.floor(payout), inline=True)

  if int(bet.winner) == 0:
    #embed.add_field(name="Winner:", value="None", inline=True)
    pass
  else:
    winner_team = ""
    if int(bet.winner) == 1:
      winner_team = bet.t1
    else:
      winner_team = bet.t2

    embed.add_field(name="Winner:", value=winner_team, inline=True)

  #date_formatted = bet.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  #embed.add_field(name="Created On:", value=date_formatted, inline=True)
  #embed.add_field(name="Match ID:", value=bet.match_id, inline=True)
  #embed.add_field(name="Visiblity:", value=("Hidden" if bet.hidden else "Shown"), inline=True)
  embed.add_field(name="ID:", value=str(bet.code), inline=True)
  return embed


def create_bet_list_embedded(embed_title, bets_ambig, show_hidden, session=None):
  if session is None:
    with Session.begin() as session:
      create_bet_list_embedded(embed_title, bets_ambig, session)
  if bets_ambig is None:
    return None
  too_many = False
  if len(bets_ambig) > 24:
    bets_ambig = bets_ambig[:24]
    too_many = True
  
  if too_many:
    embed_title = "First 24 Bets (too many to show do /match bets)"
    
  embed = discord.Embed(title=embed_title, color=discord.Color.blue())
  if all(isinstance(s, str) for s in bets_ambig):
    bets_ambig = get_mult_from_db("Bet", bets_ambig, session)
  if len(bets_ambig) == 0:
    return None
  
  bets_ambig.sort(key=lambda x: x.match.date_created)

  visible_bets = []
  hidden_bets = []
  for bet in bets_ambig:
    if bet.hidden:
      hidden_bets.append(bet)
    else:
      visible_bets.append(bet)
      
  bets_ambig = visible_bets + hidden_bets
  
  for bet in bets_ambig:
    if bet.hidden and (show_hidden == False):
      embed.add_field(name=f"{bet.user.username}'s Hidden Bet on {bet.t1} vs {bet.t2}", value=f"Teams: {bet.t1} vs {bet.t2}", inline=False)
    else:
      team = bet.get_team()
      text = f" Bet on {bet.t1} vs {bet.t2}"
      if bet.hidden:
        text = " Hidden" + text
      text = f"{bet.user.username}'s" + text
      embed.add_field(name=text, value=f"Team: {team}, Amount: {bet.amount_bet}, Payout on Win: {int(math.floor(bet.get_payout()))}", inline=False)
  return embed


def create_user_embedded(user_ambig, session=None):
  user = ambig_to_obj(user_ambig, "User", session)
  if user is None:
    return None

  embed = discord.Embed(title=f"{user.username}'s balance:", color=discord.Color.from_rgb(*hex_to_tuple(user.color_hex)))
  embed.add_field(name="Name:", value=id_to_mention(user.code), inline=False)
  embed.add_field(name="Account balance:", value=math.floor(user.balances[-1][1]), inline=True)
  embed.add_field(name="Balance Available:", value=math.floor(user.get_visible_balance(session)), inline=True)
  embed.add_field(name="Loan balance:", value=math.floor(user.loan_bal()), inline=True)
  return embed


def create_leaderboard_embedded(session=None):
  if session is None:
    with Session.begin() as session:
      create_leaderboard_embedded(session)
  users = get_condition_db("User", User.hidden == False, session)
  users = get_active_users(users, session)
  user_rankings = [(user, user.balances[-1][1]) for user in users]
  user_rankings.sort(key=lambda x: x[1], reverse=True)
  embed = discord.Embed(title="Leaderboard:", color=discord.Color.gold())
  medals = [emoji.demojize("🥇"), emoji.demojize("🥈"), emoji.demojize("🥉")]
  rank_num = 1
  for user_rank in user_rankings:
    rank = ""
    if rank_num > len(medals):
      rank = "#" + str(rank_num)
      name = user_rank[0].username
      embed.add_field(name=rank + f": {name}", value=str(math.floor(user_rank[1])), inline=False)
    else:
      rank = emoji.emojize(medals[rank_num - 1])
      name = user_rank[0].username
      embed.add_field(name=rank + f":  {name}", value=str(math.floor(user_rank[1])), inline=False)
    rank_num += 1
  return embed

  
def create_payout_list_embedded(embed_title, match, bet_user_payouts):
  embed = discord.Embed(title=embed_title, color=discord.Color.from_rgb(*hex_to_tuple(match.color_hex)))
  for bet, user, payout in bet_user_payouts:
    if payout > 0:
      value = f"Won {math.floor(payout)}. Current balance: {math.floor(user.balances[-1][1])}"
    else:
      value = f"Lost {math.floor(payout)}. Current balance: {math.floor(user.balances[-1][1])}"
    embed.add_field(name=f"{user.username} bet {bet.amount_bet} on {bet.get_team()}", value=value, inline=False)

  return embed


def create_award_label_list_embedded(user, award_labels):
  embed = discord.Embed(title=f"{user.username}'s Awards:", color=discord.Color.from_rgb(*hex_to_tuple(user.color_hex)))
  award_labels.reverse()
  award_labels = award_labels[:25]
  for award_label in award_labels:
        
    award_t = award_label.split(", ")

    name = ", ".join(award_t[:-2])

    embed.add_field(name=name, value=f"Balance changed by {award_t[-2]}, {award_t[-1]}", inline=False)
  return embed

def create_tournament_embedded(embed_title, tournament):
  embed = discord.Embed(title=embed_title, color=discord.Color.from_rgb(*hex_to_tuple(tournament.color_hex)))
  embed.add_field(name="Name:", value=tournament.name, inline=True)
  active_str = "No"
  if tournament.active:
    active_str = "Yes"
  embed.add_field(name="Active:", value=active_str, inline=True)
  embed.add_field(name="VLR Code:", value=tournament.vlr_code, inline=True)
  return embed

def create_team_embedded(embed_title, team):
  embed = discord.Embed(title=embed_title, color=discord.Color.from_rgb(*hex_to_tuple(team.color_hex)))
  embed.add_field(name="Name:", value=team.name, inline=True)
  embed.add_field(name="VLR Code:", value=team.vlr_code, inline=True)
  return embed
