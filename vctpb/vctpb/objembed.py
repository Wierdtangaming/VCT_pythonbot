import discord
from dbinterface import get_from_list, add_to_list, replace_in_list, remove_from_list, get_all_objects, smart_get_user
from Match import Match
from Bet import Bet
from User import User
from convert import ambig_to_obj, get_user_from_at, get_user_from_id, get_user_from_member, user_from_autocomplete_tuple, id_to_metion
from colorinterface import get_all_colors, hex_to_tuple, save_colors, get_color, add_color, remove_color, rename_color, recolor_color, get_all_colors_key_hex
import math
import emoji


async def create_match_embedded(match_ambig, title):
  match = ambig_to_obj(match_ambig, "match")
  if match == None:
    return None
  embed = discord.Embed(title=title, color=discord.Color.from_rgb(*hex_to_tuple(match.color)))
  embed.add_field(name="Teams:", value=match.t1 + " vs " + match.t2, inline=True)
  embed.add_field(name="Odds:", value=str(match.t1o) + " / " + str(match.t2o), inline=True)
  embed.add_field(name="Tournament Name:", value=match.tournament_name, inline=True)
  embed.add_field(name="Odds Source:", value=match.odds_source, inline=True)
  embed.add_field(name="Creator:", value=id_to_metion(match.creator), inline=True)
  bet_str = str(", ".join(match.bet_ids))
  if bet_str == "":
    bet_str = "None"
  embed.add_field(name="Bet IDs:", value=bet_str, inline=True)
  date_formatted = match.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  embed.add_field(name="Created On:", value=date_formatted, inline=True)
  if match.date_closed == None:
    embed.add_field(name="Betting Open:", value="Yes", inline=True)
  else:
    embed.add_field(name="Betting Open:", value="No", inline=True)

  if int(match.winner) == 0:
    embed.add_field(name="Winner:", value="None", inline=True)
  else:
    winner_team = ""
    if int(match.winner) == 1:
      winner_team = match.t1
    else:
      winner_team = match.t2

    embed.add_field(name="Winner:", value=winner_team, inline=True)

  embed.add_field(name="Identifier:", value=match.code, inline=False)
  return embed


async def create_match_list_embedded(embed_title, matches_ambig):
  embed = discord.Embed(title=embed_title, color=discord.Color.red())
  if all(isinstance(s, str) for s in matches_ambig):
    for match_id in matches_ambig:
      match = get_from_list("match", match_id)
      embed.add_field(name="\n" + "Match: " + match.code, value=match.short_to_string() + "\n", inline=False)
  else:
    for match in matches_ambig:
      embed.add_field(name="\n" + "Match: " + match.code, value=match.short_to_string() + "\n", inline=False)
  return embed


async def create_bet_embedded(bet_ambig, title):
  bet = ambig_to_obj(bet_ambig, "bet")
  if bet == None:
    return None

  embed = discord.Embed(title=title, color=discord.Color.from_rgb(*hex_to_tuple(bet.color)))
  embed.add_field(name="Match Identifier:", value=bet.match_id, inline=True)
  embed.add_field(name="User:", value=id_to_metion(bet.user_id), inline=True)
  embed.add_field(name="Amount Bet:", value=bet.bet_amount, inline=True)
  match = get_from_list("match", bet.match_id)
  (team, payout) = bet.get_team_and_payout()

  embed.add_field(name="Bet on:", value=team, inline=True)
  embed.add_field(name="Payout On Win:", value=math.floor(payout), inline=True)

  if int(bet.winner) == 0:
    embed.add_field(name="Winner:", value="None", inline=True)
  else:
    winner_team = ""
    if int(bet.winner) == 1:
      winner_team = match.t1
    else:
      winner_team = match.t2

    embed.add_field(name="Winner:", value=winner_team, inline=True)

  date_formatted = bet.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  embed.add_field(name="Created On:", value=date_formatted, inline=True)
  embed.add_field(name="Identifier:", value=bet.code, inline=False)
  return embed


async def create_bet_list_embedded(embed_title, bets_ambig, bot):
  embed = discord.Embed(title=embed_title, color=discord.Color.blue())
  if all(isinstance(s, str) for s in bets_ambig):
    for bet_id in bets_ambig:
      bet = get_from_list("bet", bet_id)
      embed.add_field(name="\n" + "Bet: " + bet.code, value=await bet.short_to_string(bot) + "\n", inline=False)
  else:
    for bet in bets_ambig:
      embed.add_field(name="\n" + "Bet: " + bet.code, value=await bet.short_to_string(bot) + "\n", inline=False)
  return embed


async def create_user_embedded(user_ambig):
  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return None

  embed = discord.Embed(title=f"{user.username}'s Balance:", color=discord.Color.from_rgb(*hex_to_tuple(user.color)))
  embed.add_field(name="Name:", value=id_to_metion(user.code), inline=False)
  embed.add_field(name="Account Balance:", value=math.floor(user.balance[-1][1]), inline=True)
  embed.add_field(name="Balance Available:", value=math.floor(user.get_balance()), inline=True)
  embed.add_field(name="Loan Balance:", value=math.floor(user.loan_bal()), inline=True)
  return embed


async def create_leaderboard_embedded():
  users = get_all_objects("user")
  user_rankings = [(user, user.balance[-1][1]) for user in users]
  user_rankings.sort(key=lambda x: x[1])
  user_rankings.reverse()
  embed = discord.Embed(title="Leaderboard:", color=discord.Color.gold())
  medals = [emoji.demojize("🥇"), emoji.demojize("🥈"), emoji.demojize("🥉")]
  rank_num = 1
  for user_rank in user_rankings:
    rank = ""
    if not user_rank[0].show_on_lb:
      continue
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

  
async def create_payout_list_embedded(embed_title, match, bet_user_payouts):
  embed = discord.Embed(title=embed_title, color=discord.Color.from_rgb(*hex_to_tuple(match.color)))
  for bet, user, payout in bet_user_payouts:
    if payout > 0:
      value = f"Won {math.floor(payout)}. Current balance: {math.floor(user.balance[-1][1])}"
    else:
      value = f"Lost {math.floor(payout)}. Current balance: {math.floor(user.balance[-1][1])}"
    embed.add_field(name=f"{user.username} bet {bet.bet_amount} on {bet.get_team()}", value=value, inline=False)

  return embed


def create_award_label_list_embedded(user, award_labels):
  embed = discord.Embed(title=f"{user.username}'s Awards:", color=discord.Color.from_rgb(*hex_to_tuple(user.color)))
  for award_label in award_labels:
        
    award_t = award_label.split(", ")

    name = ", ".join(award_t[:-2])

    embed.add_field(name=name, value=f"Balance changed by {award_t[-2]}, {award_t[-1]}", inline=False)
  return embed