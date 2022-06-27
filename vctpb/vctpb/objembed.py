import discord
from dbinterface import get_mult_from_db, get_condition_db
from Match import Match
from Bet import Bet
from User import User
from convert import ambig_to_obj, id_to_metion
from colorinterface import hex_to_tuple
import math
import emoji
from sqlaobjs import Session


def create_match_embedded(match_ambig, title, session=None):
  match = ambig_to_obj(match_ambig, "Match", session)
  if match is None:
    return None
  
  embed = discord.Embed(title=title, color=discord.Color.from_rgb(*hex_to_tuple(match.color_hex)))
  embed.add_field(name="Teams:", value=match.t1 + " vs " + match.t2, inline=True)
  embed.add_field(name="Odds:", value=str(match.t1o) + " / " + str(match.t2o), inline=True)
  embed.add_field(name="Tournament Name:", value=match.tournament_name, inline=True)
  embed.add_field(name="Odds Source:", value=match.odds_source, inline=True)
  embed.add_field(name="Creator:", value=id_to_metion(match.creator_id), inline=True)
  bet_codes = [bet.code for bet in match.bets]
  bet_str = str(", ".join(bet_codes))
  if bet_str == "":
    bet_str = "None"
  embed.add_field(name="Bet IDs:", value=bet_str, inline=True)
  date_formatted = match.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  embed.add_field(name="Created On:", value=date_formatted, inline=True)
  if match.date_closed is None:
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


def create_match_list_embedded(embed_title, matches_ambig, session=None):
  embed = discord.Embed(title=embed_title, color=discord.Color.red())
  if all(isinstance(s, str) for s in matches_ambig):
    matches_ambig = get_mult_from_db("Match", matches_ambig, session)
  for match in matches_ambig:
    embed.add_field(name="\n" + "Match: " + match.code, value=match.short_to_string() + "\n", inline=False)
  return embed

def create_bet_hidden_embedded(bet_ambig, title, session=None):
  if session is None:
    with Session.begin() as session:
      return create_bet_hidden_embedded(bet_ambig, title, session)
    
  bet = ambig_to_obj(bet_ambig, "Bet", session)
  if bet is None:
    return None
  
  embed = discord.Embed(title=title, color=discord.Color.from_rgb(*hex_to_tuple(bet.color_hex)))
  #when teams done this has to be diff color
  match = bet.match
  embed.add_field(name="User:", value=id_to_metion(bet.user_id), inline=True)
  embed.add_field(name="Teams:", value=match.t1 + " vs " + match.t2, inline=True)

  if int(bet.winner) == 0:
    embed.add_field(name="Winner:", value="None", inline=True)
  else:
    winner_team = ""
    if int(bet.winner) == 1:
      winner_team = bet.t1
    else:
      winner_team = bet.t2

    embed.add_field(name="Winner:", value=winner_team, inline=True)

  date_formatted = bet.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  embed.add_field(name="Created On:", value=date_formatted, inline=True)
  embed.add_field(name="Match Identifier:", value=bet.match_id, inline=True)
  embed.add_field(name="Identifier:", value=bet.code, inline=False)
  return embed


def create_bet_embedded(bet_ambig, title, session=None):
  if session is None:
    with Session.begin() as session:
      return create_bet_embedded(bet_ambig, title, session)
    
  bet = ambig_to_obj(bet_ambig, "Bet", session)
  if bet is None:
    return None
  
  embed = discord.Embed(title=title, color=discord.Color.from_rgb(*hex_to_tuple(bet.color_hex)))
  embed.add_field(name="User:", value=id_to_metion(bet.user_id), inline=True)
  embed.add_field(name="Amount Bet:", value=bet.amount_bet, inline=True)
  (team, payout) = bet.get_team_and_payout(session)

  embed.add_field(name="Bet on:", value=team, inline=True)
  embed.add_field(name="Payout On Win:", value=math.floor(payout), inline=True)

  if int(bet.winner) == 0:
    embed.add_field(name="Winner:", value="None", inline=True)
  else:
    winner_team = ""
    if int(bet.winner) == 1:
      winner_team = bet.t1
    else:
      winner_team = bet.t2

    embed.add_field(name="Winner:", value=winner_team, inline=True)

  date_formatted = bet.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  embed.add_field(name="Created On:", value=date_formatted, inline=True)
  embed.add_field(name="Match Identifier:", value=bet.match_id, inline=True)
  embed.add_field(name="Identifier:", value=bet.code, inline=False)
  return embed


def create_bet_list_embedded(embed_title, bets_ambig, session=None):
  if session is None:
    with Session.begin() as session:
      create_bet_list_embedded(embed_title, bets_ambig, session)
  if bets_ambig is None:
    return None
  embed = discord.Embed(title=embed_title, color=discord.Color.blue())
  if all(isinstance(s, str) for s in bets_ambig):
    bets_ambig = get_mult_from_db("Bet", bets_ambig, session)
  if len(bets_ambig) == 0:
    return None
  bets_ambig.sort(key=lambda x: x.match_id)
  for bet in bets_ambig:
    if bet.hidden:
      embed.add_field(name=f"{bet.user.username}'s Bet on {bet.t1} vs {bet.t2}", value = bet.short_to_hidden_string() + "\n", inline=False)
    else:
      embed.add_field(name=f"{bet.user.username}'s Bet on {bet.get_team()}", value = bet.short_to_string() + "\n", inline=False)
  return embed


def create_user_embedded(user_ambig, session=None):
  user = ambig_to_obj(user_ambig, "User", session)
  if user is None:
    return None

  embed = discord.Embed(title=f"{user.username}'s balance:", color=discord.Color.from_rgb(*hex_to_tuple(user.color_hex)))
  embed.add_field(name="Name:", value=id_to_metion(user.code), inline=False)
  embed.add_field(name="Account balance:", value=math.floor(user.balances[-1][1]), inline=True)
  embed.add_field(name="Balance Available:", value=math.floor(user.get_balance(session)), inline=True)
  embed.add_field(name="Loan balance:", value=math.floor(user.loan_bal()), inline=True)
  return embed


def create_leaderboard_embedded(session=None):
  users = get_condition_db("User", User.hidden == False, session)
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