
# add moddifacation when no on incorrect match creation
# rename, remove, get all balance_id
# double check balance rounding
# test bet list with and without await
# have it replace by code not by value
# test prefix unique with 1 long in test code


from keepalive import keep_alive

from io import BytesIO
import collections
#git clone https://github.com/Pycord-Development/pycord
#cd pycord
#python3 -m pip install -U .[voice]

#pip install git+https://github.com/Pycord-Development/pycord
import discord
from discord.commands import Option, OptionChoice, SlashCommandGroup
from discord.ui import InputText, Modal
import os
import random
import jsonpickle
from replit import db
from Match import Match
from Bet import Bet
from User import User
from dbinterface import get_from_list, add_to_list, replace_in_list, remove_from_list, get_all_objects, smart_get_user
import math
from datetime import datetime
from discord.ext import commands
import emoji

intents = discord.Intents.all()

bot = commands.Bot(intents=intents, command_prefix="$")

gid = [int(os.environ["GUILD_ID"])]
print(gid)

# matches are in match_list_[identifier] one key contains 50 matches, indentifyer incrimentaly counts up
# user is in user_list_[identifier] one key contains 50 users, indentifyer incrimentaly counts up
# bet is in bet_list_[identifier] one key contains 50 users, indentifyer incrimentaly counts up
# logs are log_[ID] holds (log, date)


def ambig_to_obj(ambig, prefix):
  if isinstance(ambig, int) or isinstance(ambig, str):
    obj = get_from_list(prefix, ambig)
  elif isinstance(ambig, discord.Member):
    obj = get_from_list(prefix, ambig.id)
  elif isinstance(ambig, User) or isinstance(ambig, Match) or isinstance(ambig, Bet):
    obj = ambig
  else:
    obj = None
    print(ambig, type(ambig))
  return obj

def get_user_from_at(id):
  uid = id.replace("<", "")
  uid = uid.replace(">", "")
  uid = uid.replace("@", "")
  uid = uid.replace("!", "")
  if uid.isdigit():
    return get_user_from_id(int(uid))
  else:
    return None

def get_user_from_id(id):
  users = get_all_objects("user")
  for user in users:
    if user.code == id:
      return user
  
  if user == None:
    return None
    
async def get_user_from_member(ctx, user):
  if user == None:
    user = ctx.author
  user = get_from_list("user", user.id)
  if user == None:
    await ctx.respond("User not found. To create an account do $balance")
  return user


async def user_from_autocorrect_tuple(ctx, t_list, text, prefix):
  obj = next((t[1] for t in t_list if text == t[0]), None)
  if obj is None:
    obj = get_from_list(prefix, text)
    
  if obj is None:
    if ctx is not None:
      await ctx.respond(f"{prefix.capitalize()} ID not found.")
  return obj


def get_all_avalable_matches():
  matches = get_all_objects("match")
  match_list = []
  for match in matches:
    if int(match.winner) == 0:
      match_list.append(match)
  return match_list

def avalable_matches_name_code():
  matches = get_all_objects("match")
  match_t_list = []
  for match in matches:
    if match.date_closed is None:
      match_t_list.append((f"{match.t1} vs {match.t2}", match))
  return match_t_list

def current_matches_name_code():
  matches = get_all_objects("match")
  match_t_list = []
  for match in matches:
    if match.winner == 0:
      match_t_list.append((f"{match.t1} vs {match.t2}", match))
  return match_t_list

async def current_bets_name_code(bot):
  matches = get_all_objects("match")
  bet_list = []
  for match in matches:
    if match.date_closed is None:
      for bet_id in match.bet_ids:
        bet = get_from_list("bet", bet_id)
        name = (await smart_get_user(bet.user_id, bot)).display_name
        bet_list.append((f"{name}: {bet.bet_amount} on {bet.get_team(match)}", bet))
  return bet_list

def get_last_tournament_name(amount):
  matches = get_all_objects("match")
  matches.reverse()
  name_set = set()
  for match in matches:
    name_set.add(match.tournament_name)
    if len(name_set) == amount:
      if amount == 1:
        return list(name_set)[0]
      return list(name_set)

def get_last_odds_source(amount):
  matches = get_all_objects("match")
  matches.reverse()
  name_set = set()
  for match in matches:
    name_set.add(match.odds_source)
    if len(name_set) == amount:
      if amount == 1:
        return list(name_set)[0]
      return list(name_set)

      
def rename_balance_id(user_ambig, balance_id, new_balance_id):
  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return "User not found"
  indices = [i for i, x in enumerate(user.balance) if x[0] == balance_id]
  if len(indices) > 1:
    return "More than one balance_id found"
  elif len(indices) == 0:
    return "No balance_id found"
  else:
    balat = user.balance[indices[0]]
    user.balance[indices[0]] = (new_balance_id, balat[1], balat[2])
    replace_in_list("user", user.code, user)


def delete_balance_id(user_ambig, balance_id):
  print(balance_id)
  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return "User not found"
  indices = [i for i, x in enumerate(user.balance) if x[0] == balance_id]
  if len(indices) > 1:
    print("More than one balance_id found")
  elif len(indices) == 0:
    return "No balancen id found"
  reset_range = user.get_to_reset_range(indices[0])
  
  index = indices[0]
  diff = user.balance[index][1] - user.balance[index-1][1]
  print(diff)
  for i in reset_range:
    bal_list = list(user.balance[i])
    bal_list[1] = bal_list[1] - diff
    user.balance[i] = tuple(bal_list)
  balat = user.balance[indices[0]]
  
  user.balance.remove(balat)
  replace_in_list("user", user.code, user)


def print_all_balance(user_ambig):
  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return None

  [print(bal[0], bal[1]) for bal in user.balance]


async def edit_all_messages(ids, embedd):
  for id in ids:
    try:
      channel = await bot.fetch_channel(id[1])
      msg = await channel.fetch_message(id[0])
      await msg.edit(embed=embedd)
    except Exception:
      print(id, "no msg found")

async def delete_all_messages(ids):
  for id in ids:
    try:
      channel = await bot.fetch_channel(id[1])
      msg = await channel.fetch_message(id[0])
      await msg.delete()
    except Exception:
      print(id, "no msg found")

def is_key(key):
  keys = db.keys()
  return key in keys


def is_digit(str):
  try:
    int(str)
    return True
  except ValueError:
    return False

def to_float(str):
  try:
    f = float(str)
    return f
  except ValueError:
    return None

def get_uniqe_code(prefix):
  all_objs = get_all_objects(prefix)
  codes = [str(k.code) for k in all_objs]
  code = ""
  copy = True
  while copy:
    copy = False

    random.seed()
    code = str(hex(random.randint(0, 2**32 - 1))[2:]).zfill(8)
    for k in codes:
      if k == code:
        copy = True
  return code


def create_user(user_id):
  random.seed()
  color_code = str(hex(random.randint(0, 2**32 - 1))[2:]).zfill(8)
  user = User(user_id, color_code, datetime.now())
  add_to_list("user", user)
  return user


#color start
def hex_to_color():
  print("1")
  
def get_all_colors():
  print("1")
  
def get_color(name):
  print("1")
  
def add_color(name, hex):
  print("1")
  
def remove_color(name):
  print("1")
  
def rename_color(old_name, new_name):
  print("1")
  
def recolor_color(name):
  print("1")
  #color end



async def create_match_embedded(match_ambig):
  match = ambig_to_obj(match_ambig, "match")
  if match == None:
    return None

  embed = discord.Embed(title="Match:", color=discord.Color.from_rgb(*tuple(int((match.code[0:8])[i : i + 2], 16) for i in (0, 2, 4))))

  embed.add_field(name="Teams:", value=match.t1 + " vs " + match.t2, inline=True)
  embed.add_field(name="Odds:", value=str(match.t1o) + " / " + str(match.t2o), inline=True)
  embed.add_field(name="Tournament Name:", value=match.tournament_name, inline=True)
  embed.add_field(name="Odds Source:", value=match.odds_source, inline=True)
  embed.add_field(name="Creator:", value=(await smart_get_user(match.creator, bot)).mention, inline=True)
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


async def create_bet_list_embedded(embed_title, bets_ambig):
  embed = discord.Embed(title=embed_title, color=discord.Color.red())
  if all(isinstance(s, str) for s in bets_ambig):
    for bet_id in bets_ambig:
      bet = get_from_list("bet", bet_id)
      embed.add_field(name="\n" + "Bet: " + bet.code, value=await bet.short_to_string(bot) + "\n", inline=False)
  else:
    for bet in bets_ambig:
      embed.add_field(name="\n" + "Bet: " + bet.code, value=await bet.short_to_string(bot) + "\n", inline=False)
  return embed


async def create_bet_embedded(bet_ambig):
  bet = ambig_to_obj(bet_ambig, "bet")
  if bet == None:
    return None

  embed = discord.Embed(title="Bet:", color=discord.Color.from_rgb(*tuple(int((bet.code[0:8])[i : i + 2], 16) for i in (0, 2, 4))))
  embed.add_field(name="Match Identifier:", value=bet.match_id, inline=True)
  embed.add_field(name="User:", value=(await smart_get_user(bet.user_id, bot)).mention, inline=True)
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


async def create_user_embedded(user_ambig):
  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return None

  embed = discord.Embed(title="User:", color=discord.Color.from_rgb(*tuple(int((user.color_code[0:8])[i : i + 2], 16) for i in (0, 2, 4))))
  embed.add_field(name="Name:", value=(await smart_get_user(user.code, bot)).mention, inline=False)
  embed.add_field(name="Account Balance:", value=math.floor(user.balance[-1][1]), inline=True)
  embed.add_field(name="Balance Available:", value=math.floor(user.get_balance()), inline=True)
  embed.add_field(name="Loan Balance:", value=math.floor(user.loan_bal()), inline=True)
  return embed


async def create_leaderboard_embedded():
  users = get_all_objects("user")
  user_rankings = [(user.code, user.balance[-1][1]) for user in users]
  user_rankings.sort(key=lambda x: x[1])
  user_rankings.reverse()
  embed = discord.Embed(title="Leaderboard:", color=discord.Color.gold())
  medals = [emoji.demojize("🥇"), emoji.demojize("🥈"), emoji.demojize("🥉")]
  rank_num = 1
  for user_rank in user_rankings:
    rank = ""
    if rank_num > len(medals):
      rank = "#" + str(rank_num)
      embed.add_field(name=rank + f": {(await smart_get_user(user_rank[0], bot)).display_name}", value=str(math.floor(user_rank[1])), inline=False)
    else:
      rank = emoji.emojize(medals[rank_num - 1])
      embed.add_field(name=rank + f":  {(await smart_get_user(user_rank[0], bot)).display_name}", value=str(math.floor(user_rank[1])), inline=False)
    rank_num += 1
  return embed


def add_to_active_ids(user_ambig, bet_ambig):
  if (user := ambig_to_obj(user_ambig, "user")) is None: return None
  if (bet := ambig_to_obj(bet_ambig, "bet")) is None: return None

  user.active_bet_ids.append((bet.code, bet.match_id))
  replace_in_list("user", user.code, user)


def remove_from_active_ids(user_ambig, bet_id):
  if (user := ambig_to_obj(user_ambig, "user")) is None: return None
  
  if (t := next((t for t in user.active_bet_ids if bet_id == t[0]), None)) is None:
    print("Bet_id Not Found")
    return
  user.active_bet_ids.remove(t)
  replace_in_list("user", user.code, user)


def add_balance_user(user_ambig, change, description, date):
  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return None
  user.balance.append((description, round(user.balance[-1][1] + change, 5), date))
  replace_in_list("user", user.code, user)
  return user

#returns user with new balance
def change_prev_balance(user, balance_id, new_amount):
  index = [x for x, y in enumerate(user.balance) if y[0] == str(balance_id)]
  if not len(index) == 1:
    print(str(len(index)) + " copy of id")
    return None
    
  index = index[0]

  difference = user.balance[index][1] - new_amount

  for i in range(index, len(user.balance)):
    if i+1 < len(user.balance):
      difference = user.balance[i+1][1] - user.balance[i][1]
    user.balance[i] = (user.balance[i][0], new_amount, user.balance[i][2])
    new_amount = user.balance[i][1] + difference
  return user
  
  
def backup():
  keys = db.keys()
  for key in keys:
    print(f"backing up {key}")
    db[f"backup_{key}"] = db[key]
  print("backed up all keys")
  




def roundup(x):
  return int(math.ceil(x * 1000)) / 1000


@bot.event
async def on_ready():
  print("Logged in as {0.user}".format(bot))
  print(bot.guilds)


@bot.event
async def on_message(message):

  if message.author == bot.user:
    return

  print(message.author, message.content)
  await bot.process_commands(message)

  if message.content.startswith("$"):
    return
    
  rand = random.randint(0, 50)
  if rand == 0:
    backup()

  

#choices start
yes_no_choices = [
  OptionChoice(name="yes", value=0),
  OptionChoice(name="no", value=1),
]
list_choices = [
  OptionChoice(name="shortened", value=0),
  OptionChoice(name="full", value=1),
]
open_close_choices = [
  OptionChoice(name="open", value=0),
  OptionChoice(name="close", value=1),
]
#choices end

    
#match start
match = SlashCommandGroup(
  name = "match", 
  description = "Create, edit, and view matches.",
  guild_ids = gid,
)

#match modal start
class MatchModal(Modal):
  
  def __init__(self, balance_odds=True, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    
    self.balance_odds = balance_odds
    
    self.add_item(InputText(label="Enter team one name.", placeholder='Get from VLR', min_length=1, max_length=100))
    self.add_item(InputText(label="Enter team two name.", placeholder='Get from VLR', min_length=1, max_length=100))
    
    self.add_item(InputText(label="Enter odds. Team 1 odds/Team 2 odds.", placeholder='eg: "2.34/1.75" or "1.43 3.34".', min_length=1, max_length=12))
    self.add_item(InputText(label="Enter tournament name.", value=get_last_tournament_name(1), min_length=1, max_length=300))
    
    self.add_item(InputText(label="Enter odds source.", value=get_last_odds_source(1), min_length=1, max_length=100))

  
  async def callback(self, interaction: discord.Interaction):
    team_one = self.children[0].value.strip()
    team_two = self.children[1].value.strip()
    odds_combined = self.children[2].value.strip()
    tournament_name = self.children[3].value.strip()
    betting_site = self.children[4].value.strip()
    
    print(f"-{team_one}-")
    if odds_combined.count(" ") > 1:
      odds_combined.strip(" ")
      
    splits = [" ", "/", "\\", ";", ":", ",", "-", "_", "|"]
    for spliter in splits:
      print(spliter)
      if odds_combined.count(spliter) == 1:
        team_one_old_odds, team_two_old_odds = "".join(_ for _ in odds_combined if _ in f".1234567890{spliter}").split(spliter)
        break
    else:
      await interaction.response.send_message(f"Odds are not valid. Odds must be [odds 1]/[odds 2].")
      return
    print(team_one_old_odds, team_two_old_odds)
    print(to_float(team_one_old_odds), to_float(team_two_old_odds))
    if (to_float(team_one_old_odds) is None) or (to_float(team_two_old_odds) is None): 
      await interaction.response.send_message(f"Odds are not valid. Odds must be [odds 1]/[odds 2].")
      return
    team_one_old_odds = to_float(team_one_old_odds)
    team_two_old_odds = to_float(team_two_old_odds)
    if team_one_old_odds <= 1 or team_two_old_odds <= 1:
      await interaction.response.send_message(f"Odds must be greater than 1.")
      return
    if self.balance_odds == 0:
      odds1 = 1 / team_one_old_odds
      odds2 = 1 / team_two_old_odds
    
      percentage1 = odds1 / (odds1 + odds2)
      percentage2 = odds2 / (odds1 + odds2)
    
      odds1 = 1 / percentage1
      odds2 = 1 / percentage2
    
      team_one_odds = roundup(odds1)
      team_two_odds = roundup(odds2)
    else:
      team_one_odds = team_one_old_odds
      team_two_odds = team_two_old_odds
      
    print(team_one_odds, team_two_odds)
    
    code = get_uniqe_code("match")
  
    
    match = Match(team_one, team_two, team_one_old_odds, team_two_old_odds, team_one_odds, team_two_odds, tournament_name, betting_site, interaction.user.id, datetime.today(), code)

    
    
    #date_formatted = cmatch.date_created.strftime("%m/%d/%Y %H:%M:%S")
    #s += "Teams: " + str(cmatch.t1) + " vs " + str(cmatch.t2) + "\nOdds: " + str(cmatch.t1o) + " / " + str(cmatch.t2o) + "\nTournament Name: " + str(cmatch.tournament_name) + "\nOdds Source: " + str(cmatch.odds_source) + "\nCreator: " + str((await smart_get_user(cmatch.creator, bot)).mention) + "\nCreated On: " + str(date_formatted)

    #add confirm button
    
    embedd = await create_match_embedded(match)

    if (channel := await bot.fetch_channel(db["match_channel_id"])) == interaction.channel:
      inter = await interaction.response.send_message(embed=embedd)
      msg = await inter.original_message()
    else:
      msg = await channel.send(embed=embedd)
      await interaction.response.send_message(f"Match created in {channel.mention}.")
      
    match.message_ids.append((msg.id, msg.channel.id))
    add_to_list("match", match)
    
#match modal end
    
#tournament autocomplete start (unused)
async def tournament_list_autocomplete(ctx: discord.AutocompleteContext):
  return get_last_tournament_name(5)
#tournament autocomplete end (unused)

#match list autocomplete start
async def match_list_autocomplete(ctx: discord.AutocompleteContext):
  match_t_list = current_matches_name_code()
  auto_completes = [match_t[0] for match_t in match_t_list if (ctx.value.lower() in match_t[0].lower())]
  return auto_completes
#match list autocomplete end
  

#match open close list autocomplete start
async def match_open_close_list_autocomplete(ctx: discord.AutocompleteContext):
  type = ctx.options["type"]
  match_t_list = current_matches_name_code()
  if type is None:
    auto_completes = [match_t[0] for match_t in match_t_list if (ctx.value.lower() in match_t[0].lower())]
  elif type == 0:
    auto_completes = [match_t[0] for match_t in match_t_list if ((ctx.value.lower() in match_t[0].lower()) and (match_t[1].date_closed is not None))]
  else:
    auto_completes = [match_t[0] for match_t in match_t_list if ((ctx.value.lower() in match_t[0].lower()) and (match_t[1].date_closed is None))]
  return auto_completes
#match open close list autocomplete end

  
#match match team autocomplete start
async def match_team_list_autocomplete(ctx: discord.AutocompleteContext):
  print(ctx.focused)
  match = ctx.options["match"]
  if match is None: return []
  if (match := await user_from_autocorrect_tuple(None, current_matches_name_code(), match, "match")) is None: return []
  auto_completes = [match.t1, match.t2]
  return auto_completes
#match match team autocomplete end

  
#match create start
@match.command(name = "create", description = "Create a match.")
async def match_create(ctx, balance_odds: Option(int, "Balance the odds? Defualt is Yes.", choices = yes_no_choices, default=True, required=False)):
    
  match_modal = MatchModal(balance_odds=balance_odds, title="Create Match")
  await ctx.interaction.response.send_modal(match_modal)
  #await match_modal.wait()
#match create end


#match find start
@match.command(name = "find", description = "Sends the embed of the match.")
async def match_find(ctx, match: Option(str, "Match you want embed of.", autocomplete=match_list_autocomplete)):
  #to do list some old ones
  if (match := await user_from_autocorrect_tuple(ctx, current_matches_name_code(), match, "match")) is None: return
  
  embedd = await create_match_embedded(match)
  inter = await ctx.respond(embed=embedd)
  msg = await inter.original_message()
  
  match.message_ids.append((msg.id, msg.channel.id))
  replace_in_list("match", match.code, match)
  
#match find end

  
#match betting start
@match.command(name = "betting", description = "Open and close betting.")
async def match_betting(ctx, type: Option(int, "Set to open or close", choices = open_close_choices), match: Option(str, "Match you want to open/close.", autocomplete=match_open_close_list_autocomplete)):

  if (match := await user_from_autocorrect_tuple(ctx, current_matches_name_code(), match, "match")) is None: return

  #if already on dont do anything complex
    
  if type == 0:
    match.date_closed = None
    await ctx.respond(f"{match.t1} vs {match.t2} betting has opened.")
  else:
    match.date_closed = datetime.now()
    await ctx.respond(f"{match.t1} vs {match.t2} betting has closed.")
  replace_in_list("match", match.code, match)
  embedd = await create_match_embedded(match)
  await edit_all_messages(match.message_ids, embedd)
#match betting end


#match winner start
@match.command(name = "winner", description = "Set winner of match.")
async def match_winner(ctx, match: Option(str, "Match you want to set winner of.", autocomplete=match_list_autocomplete), team: Option(str, "Team to set to winner.", autocomplete=match_team_list_autocomplete)):
  
  if (match := await user_from_autocorrect_tuple(ctx, current_matches_name_code(), match, "match")) is None: return
  team.strip()
  if (team == 1) or (team == match.t1):
    team = 1
  elif (team == 2) or (team == match.t2):
    team = 2
  else:
    await ctx.respond(f"Invalid team name of {team} please enter {match.t1} or {match.t2}.")
  
  if int(match.winner) != 0:
    await ctx.respond(f"Winner has already been set to {match.winner_name()}")

  match.winner = team
  time = datetime.now()
  
  match.date_winner = time
  if match.date_closed is None:
    match.date_closed = time
    
  replace_in_list("match", match.code, match)
  embedd = await create_match_embedded(match)
  await edit_all_messages(match.message_ids, embedd)
  
  odds = 0.0
  #change when autocomplete
  if team == 1:
    odds = match.t1o
    await ctx.respond("Winner has been set to " + match.t1)
  else:
    odds = match.t2o
    await ctx.respond("Winner has been set to " + match.t2)

  msg_ids = []
  users = []
  date = datetime.now()
  for bet_id in match.bet_ids:
    bet = get_from_list("bet", bet_id)
    if not bet == None:
      #to do print out embedds of bets
      bet.winner = int(match.winner)
      payout = -bet.bet_amount
      if bet.team_num == team:
        payout += bet.bet_amount * odds
      user = get_from_list("user", bet.user_id)
      remove_from_active_ids(user, bet.code)
      add_balance_user(user, payout, "id_" + str(bet.code), date)

      replace_in_list("bet", bet.code, bet)
      embedd = await create_bet_embedded(bet)
      msg_ids.append((bet.message_ids, embedd))
      users.append(user.code)
    else:
      print(f"where the bet_id from {bet_id}")

  no_same_list_user = []
  [no_same_list_user.append(x) for x in users if x not in no_same_list_user]
  for user in no_same_list_user:
    embedd = await create_user_embedded(user)
    await ctx.send(embed=embedd)

  [await edit_all_messages(tup[0], tup[1]) for tup in msg_ids]
#match winner end


#match delete start
@match.command(name = "delete", description = "Delete a match. Can only be done if betting is open.")
async def match_delete(ctx, match: Option(str, "Match you want to set winner of.", autocomplete=match_list_autocomplete)):
  
  if (match := await user_from_autocorrect_tuple(ctx, current_matches_name_code(), match, "match")) is None: return
  if match.winner != 0:
    await ctx.respond(f"Match winner has already been decided, you cannot delete the match.")
    return
    
  gen_msg = await ctx.respond("Deleting match...")
    
  for bet_id in match.bet_ids:
    bet = get_from_list("bet", bet_id)
    await delete_all_messages(bet.message_ids)
    remove_from_active_ids(bet.user_id, bet.code)
    remove_from_list("bet", bet)
  
  await delete_all_messages(match.message_ids)
  remove_from_list("match", match)
  await gen_msg.edit_original_message(content=f"Deleted { match.basic_to_string()}, and all bets on the match.")
#match end


#match list start
@match.command(name = "list", description = "Sends embed with all matches. If type is full it sends the whole embed of each match.")
async def match_list(ctx, type: Option(int, "If type is full it sends the whole embed of each match.", choices = list_choices, default = 0, required = False)):
  matches = get_all_objects("match")
  match_list = []
  for match in matches:
    if int(match.winner) == 0:
      match_list.append(match)
  if len(match_list) == 0:
    await ctx.respond("No undecided matches.")
    return

  if type == 0:
    #short
    gen_msg = await ctx.respond("Generating list...")
    embedd = await create_match_list_embedded("Matches:", match_list)
    await gen_msg.edit_original_message(content = "", embed=embedd)
    
  elif type == 1:
    #full
    for i, match in enumerate(match_list):
      embedd = await create_match_embedded(match)
      if i == 0:
        inter = await ctx.respond(embed=embedd)
        msg = await inter.original_message()
      else:
        msg = await ctx.interaction.followup.send(embed=embedd)
      match.message_ids.append((msg.id, msg.channel.id))
      replace_in_list("match", match.code, match)
#match list end

  
bot.add_application_command(match)
#match end
    
  
#bet start
bet = SlashCommandGroup(
  name = "bet", 
  description = "Create, edit, and view bets.",
  guild_ids = gid,
)

#bet modal start
class BetModal(Modal):
  
  def __init__(self, match: Match, user: User, error=[None, None], *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.match = match
    self.user = user
    
    if error[0] is None: 
      team_label = f"{match.t1} vs {match.t2}. Odds: {match.t1o} / {match.t2o}"
    else:
      team_label = error[0]
      
    self.add_item(InputText(label=team_label, placeholder=f'"1" for {match.t1} and "2" for {match.t2}', min_length=1, max_length=100))

    if error[1] is None: 
      amount_label = "Amount you want to bet."
    else:
      amount_label = error[1]
    self.add_item(InputText(label=amount_label, placeholder=f"Your avalable balance is {math.floor(user.get_balance())}", min_length=1, max_length=20))

  async def callback(self, interaction: discord.Interaction):
    
    match = self.match
    user = self.user
    team_num = self.children[0].value
    amount = self.children[1].value
    error = [None, None]
    
    if not is_digit(amount):
      print("Amount has to be a positive whole integer.")
      error[1] = "Amount must be a positive whole number."
    
    if not (int(team_num) == 1 or int(team_num) == 2 or team_num.lower() == match.t1.lower() or team_num.lower() == match.t2.lower()):
      print("Team num has to either be 1 or 2.")
      error[0] = f'Please enter "1", "2", "{match.t1}", or "{match.t2}". Odds: {match.t1o} / {match.t2o}.'

    if int(amount) <= 0:
      print("Cant bet negatives.")
      error[1] = "Amount must be a positive whole number."

    if not match.date_closed == None:
      await interaction.response.send_message("Betting has closed you cannot make a bet.")

    code = get_uniqe_code("bet")

    balance_left = user.get_balance() - int(amount)
    if balance_left < 0:
      print("You have bet " + str(math.floor(-balance_left)) + " more than you have.")
      error[1] = "You have bet " + str(math.floor(-balance_left)) + " more than you have."
      print("⛔")
    if not error == [None, None]:
      errortxt = ""
      if error[0] is not None:
        errortext += error[0]
        if error[1] is not None:
          errortext += " "
        #TODO
        interaction.response.sent_msg(interaction)
      if error[1] is not None:
        errortext += error[1]
      return

    bet = Bet(code, match.code, user.code, int(amount), int(team_num), datetime.now())

    match.bet_ids.append(bet.code)
    add_to_active_ids(user.code, bet)

    embedd = await create_bet_embedded(bet)
    
    if (channel := await bot.fetch_channel(db["bet_channel_id"])) == interaction.channel:
      inter = await interaction.response.send_message(embed=embedd)
      msg = await inter.original_message()
    else:
      msg = await channel.send(embed=embedd)
      await interaction.response.send_message(f"Bet created in {channel.mention}.")

    bet.message_ids.append((msg.id, msg.channel.id))
    replace_in_list("match", match.code, match)
    add_to_list("bet", bet)
    embedd = await create_match_embedded(match)
    await edit_all_messages(match.message_ids, embedd)
    self.stop()
#bet modal end

  
#new match list autocomplete start
async def new_match_list_autocomplete(ctx: discord.AutocompleteContext):
  match_t_list = avalable_matches_name_code()
  if (user := get_from_list("user", ctx.interaction.user.id)) is None: return [match_t[0] for match_t in match_t_list if (ctx.value.lower() in match_t[0].lower())]
  active_bet_ids_matches = user.active_bet_ids_matches()
  auto_completes = [match_t[0] for match_t in match_t_list if (ctx.value.lower() in match_t[0].lower() and (match_t[1].code not in active_bet_ids_matches))]
  return auto_completes
#new match list autocomplete end

#bet list autocomplete start
async def bet_list_autocomplete(ctx: discord.AutocompleteContext):
  bet_t_list = await current_bets_name_code(bot)
  auto_completes = [bet_t[0] for bet_t in bet_t_list if ctx.value.lower() in bet_t[0].lower() if ctx.interaction.user.id == bet_t[1].user_id]
  return auto_completes
#bet list autocomplete end


#bet create start
@bet.command(name = "create", description = "Create a bet.")
async def bet_create(ctx, match: Option(str, "Match you want to bet on.",  autocomplete=new_match_list_autocomplete)):
  user = get_from_list("user", ctx.author.id)
  if user == None:
    create_user(ctx.author.id)
    
  if (match := await user_from_autocorrect_tuple(ctx, avalable_matches_name_code(), match, "match")) is None: return
  print(match)
    
  if match.date_closed is not None:
    await ctx.respond("Betting has closed.")
    return
    
  bet_modal = BetModal(match=match, user=user, title="Create Bet")
  await ctx.interaction.response.send_modal(bet_modal)
  await bet_modal.wait()
#bet create end


#bet cancel start
@bet.command(name = "cancel", description = "Cancels a bet if betting is open on the match.")
async def bet_cancel(ctx, bet: Option(str, "Bet you want to cancel.", autocomplete=bet_list_autocomplete)):
  if (bet := await user_from_autocorrect_tuple(ctx, await current_bets_name_code(bot), bet, "bet")) is None: return
  
  match = get_from_list("match", bet.match_id)
  if (match is None) or (match.date_closed is not None):
    await ctx.respond("Match betting has closed, you cannot cancel the bet.")
    return
    
  gen_msg = await ctx.respond("Cancelling bet...")
    
  try:
    match.bet_ids.remove(bet.code)
    replace_in_list("match", match.code, match)
    embedd = await create_match_embedded(match)
    await edit_all_messages(match.message_ids, embedd)
  except:
    print(f"{bet.code} is not in match {match.code} bet ids {match.bet_ids}")
    
  
  await delete_all_messages(bet.message_ids)
  remove_from_active_ids(bet.user_id, bet.code)
  bet = remove_from_list("bet", bet.code)
  await gen_msg.edit_original_message(content=f"Canceled {await bet.basic_to_string(bot, match)}.")
#bet cancel end


#bet find start
@bet.command(name = "find", description = "Sends the embed of the bet.")
async def bet_find(ctx, bet: Option(str, "Bet you get embed of.", autocomplete=bet_list_autocomplete)):
  #list some old matches
  if (bet := await user_from_autocorrect_tuple(ctx, await current_bets_name_code(bot), bet, "bet")) is None: return
  
  embedd = await create_bet_embedded(bet)
  inter = await ctx.respond(embed=embedd)
  msg = await inter.original_message()
  bet.message_ids.append((msg.id, msg.channel.id))
  replace_in_list("bet", bet.code, bet)
#bet find end


#bet list start
@bet.command(name = "list", description = "Sends embed with all bets. If type is full it sends the whole embed of each bet.")
async def bet_list(ctx, type: Option(int, "If type is full it sends the whole embed of each bet.", choices = list_choices, default = 0, required = False)):
  
  bets = get_all_objects("bet")
  bet_list = []
  for bet in bets:
    if int(bet.winner) == 0:
      bet_list.append(bet)
  if len(bet_list) == 0:
    await ctx.respond("No undecided bets.")
    return

  if type == 0:
    #short
    gen_msg = await ctx.respond("Generating list...")
    embedd = await create_bet_list_embedded("Bets:", bet_list)
    await gen_msg.edit_original_message(content = "", embed=embedd)
    
  elif type == 1:
    #full
    for i, bet in enumerate(bet_list):
      embedd = await create_bet_embedded(bet)
      if i == 0:
        inter = await ctx.respond(embed=embedd)
        msg = await inter.original_message()
      else:
        msg = await ctx.interaction.followup.send(embed=embedd)
      bet.message_ids.append((msg.id, msg.channel.id))
      replace_in_list("bet", bet.code, bet)
#bet list end
  
bot.add_application_command(bet)
#bet end



#assign start
assign = SlashCommandGroup(
  name = "assign", 
  description = "Assigns the discord channel it is put in to that channel type.",
  guild_ids = gid,
)

#assign matches start
@assign.command(name = "matches", description = "Where the end matches show up.")
async def assign_matches(ctx):
  db["match_channel_id"] = ctx.channel.id
  await ctx.respond("This channel is now the match list channel.")
#assign matches end

#assign bets start
@assign.command(name = "bets", description = "Where the end bets show up.")
async def assign_bets(ctx):
  db["bet_channel_id"] = ctx.channel.id
  await ctx.respond("This channel is now the bet list channel.")
#assign bets end

bot.add_application_command(assign)
#assign end



#award start
@bot.slash_command( 
  name = "award", 
  description = """Awards the money to someone's account. DON'T USE WITHOUT PERMISSION!""",
  guild_ids = gid,
)
async def award(ctx, user: Option(discord.Member, "User you wannt to award"), amount: Option(int, "Amount you want to give or take."), description: Option(str, "Uniqe description of why the award is given.")):

  if (user := await get_user_from_member(ctx, user)) is None: return
  
  abu = add_balance_user(user, amount, "award_" + description, datetime.now())
  if abu == None:
    await ctx.respond("User not found.")
  else:
    embedd = await create_user_embedded(user)
    await ctx.respond(embed=embedd)
#award end

  

#balance start
@bot.slash_command(name = "balance", description = "Shows the last x amount of balance changes (awards, bets, etc).", aliases=["bal"])
async def balance(ctx, user: Option(discord.Member, "User you want to get balance of.", default = None, required = False)):
  if user == None:
    user = get_from_list("user", ctx.author.id)
    if user == None:
      create_user(ctx.author.id)
  else:
    user = get_from_list("user", user.id)
    if user == None:
      await ctx.respond("User does not have an account yet. To create an acccount they must do $balance.")
      return
    
  embedd = await create_user_embedded(user)
  if embedd == None:
    await ctx.respond("User not found.")
    return
  await ctx.respond(embed=embedd)
#balance end



#graph start
graph = SlashCommandGroup(
  name = "graph", 
  description = "Shows an image of a graph to user.",
  guild_ids = gid,
)


#graph balance start
balance_choices = [
  OptionChoice(name="season", value=0),
  OptionChoice(name="all", value=1),
  OptionChoice(name="last", value=2),
]
@graph.command(name = "balance", description = "Gives a graph of value over time. No value in type gives you the current season.")
async def graph_balance(ctx,
  type: Option(int, "User you want to get balance of.", choices = balance_choices, default = 0, required = False), 
  user: Option(discord.Member, "User you want to get balance of.", default = None, required = False),
  amount: Option(int, "User you want to get balance of.", default = 20, required = False)):
    
  if (user := await get_user_from_member(ctx, user)) is None: return
  
  if type == 0:
    graph_type = "current"
  elif type == 1:
    graph_type = "all"
  elif type == 2:
    graph_type = amount
  else:
    ctx.respond("Not a valid type.")
    return
    
  with BytesIO() as image_binary:
    gen_msg = await ctx.respond("Generating graph...")
    user.get_graph_image(graph_type).save(image_binary, 'PNG')
    image_binary.seek(0)
    await gen_msg.edit_original_message(content = "", file=discord.File(fp=image_binary, filename='image.png'))
#graph balance end

bot.add_application_command(graph)
#graph end



#leaderboard start
@bot.slash_command(name = "leaderboard", description = "Gives leaderboard of balances.")
async def leaderboard(ctx):
  embedd = await create_leaderboard_embedded()
  await ctx.respond(embed=embedd)
#leaderboard end


  
#log start
@bot.slash_command(name = "log", description = "Shows the last x amount of balance changes (awards, bets, etc)")
async def log(ctx, amount: Option(int, "How many balance changed you want to see."), user: Option(discord.Member, "User you want to check log of (defaulted to you).", default = None, required = False)):

  if (user := await get_user_from_member(ctx, user)) is None: return
  
  if amount <= 0:
    await ctx.respond("Amount has to be greater than 0.")
    return
    
  gen_msg = await ctx.respond("Generating log...")
  
  embedds = user.get_new_balance_changes_embeds(amount)
  if embedds == None:
    await gen_msg.edit_original_message(content = "No log generated.")
    return
  
  await gen_msg.edit_original_message(content="", embeds=embedds)
#log end



#loan start
loan = SlashCommandGroup(
  name = "loan", 
  description = "Create and pay off loans.",
  guild_ids = gid,
)


#loan create start
@loan.command(name = "create", description = "Gives you 50 and adds a loan that you have to pay 50 to close you need less that 100 to get a loan.")
async def loan_create(ctx):
    
  if (user := await get_user_from_member(ctx, ctx.author)) is None: return

  if user.get_clean_bal_loan() >= 100:
    await ctx.respond("You must have less than 100 to make a loan")
    return
  user.loans.append((50, datetime.now, None))
  replace_in_list("user", user.code, user)
  await ctx.respond("You have been loaned 50")
#loan create end

  
#loan count start
@loan.command(name = "count", description = "See how many loans you have active.")
async def loan_count(ctx, user: Option(discord.Member, "User you want to get loan count of.", default = None, required = False)):
  if (user := await get_user_from_member(ctx, user)) is None: return
  
  user = get_from_list("user", ctx.author.id)
  await ctx.respond(f"You currently have {len(user.get_open_loans())} active loans")
#loan count end

  
#loan pay start
@loan.command(name = "pay", description = "See how many loans you have active.")
async def loan_pay(ctx):
  if (user := await get_user_from_member(ctx, ctx.author)) is None: return
    
  loan_amount = user.loan_bal()
  if loan_amount == 0:
    await ctx.respond("You currently have no loans")
    return
  anb = user.get_balance()
  if(anb < loan_amount):
    await ctx.respond(f"You need {math.ceil(loan_amount - anb)} more to pay off all loans")
    return

  loans = user.get_open_loans()
  for loan in loans:
    new_loan = list(loan)
    new_loan[2] = datetime.now()
    new_loan = tuple(new_loan)


    index = user.loans.index(loan)
    user.loans[index] = new_loan
  replace_in_list("user", user.code, user)
  await ctx.respond(f"You have paid off {len(loans)} loan(s)")
#loan pay end

bot.add_application_command(loan)
#loan end


#backup
@bot.command()
async def backup_db(ctx):
  backup()
  


#season reset command
@bot.command()
async def reset_season(ctx):
  # to do make the command also include season name
  return
  users = get_all_objects("user")
  date = datetime.now()
  for user in users:
    user.balance.pop()
    user.balance.append(("reset 2", 500, date))
    replace_in_list("user", user.code, user)

#debug
@bot.command()
async def debug(ctx, *args):
  if len(args) == 1:
    if args[0] == "help":
      await ctx.send(
        """IF YOU ARE NOT PIG DONT MESS WITH DEBUG, WHAT YOU NEED IS SOMEWHERE ELSE PLEASE DON'T BREAK MY DATABASE
$debug list [match, user, bet]: gives all info on all of object
$debug keys: gives all keys
$debug key "[key]": prints key as is (quotes only needed if there is a space)
$debug reassign "[original key]" "[new key]": replaces the original key with the new key (quotes only needed if there is a space)
$debug delete key "[key]": deletes key for database (quotes only needed if there is a space)
$debug balance print [user @]: prints balance to console
$debug balance delete [user @] "balance id: delete balance with that ID
$debug balance rename [user @] "old balance id" "new balance id": replaces balance ID with new ID
$debug user_dump: prints json dump"""
      )

    elif args[0] == "keys":
      await ctx.send(str(db.keys())[1:-1])

    elif args[0] == "user_dump":
      user = get_from_list("user", ctx.author.id)
      print(jsonpickle.encode(user))

    else:
      await ctx.send("Not valid command. Use $debug help to get list of commands")

  elif len(args) == 2:

    if args[0] == "list" and (args[1] == "match" or args[1] == "user" or args[1] == "bet"):
      objects = get_all_objects(args[1])
      output = ""
      for obj in objects:
        output += obj.to_string() + "\n"
      if not output == "":
        print(output)
      else:
        await ctx.send("No keys of type " + args[1])

    elif args[0] == "key":
      print(str(db[args[1]]))

    else:
      await ctx.send("Not valid command. Use $debug help to get list of commands")

  elif len(args) == 3:
    uid = get_user_from_at(args[2])
    if args[0] == "reassign":
      db[args[2]] = db[args[1]]
      del db[args[1]]
      await ctx.send("key " + args[1] + " is now " + args[2])

    elif args[0] == "delete" and args[1] == "key":
      del db[args[2]]
      await ctx.send("deleted " + str(args[2]))

    elif args[0] == "balance" and args[1] == "print" and not uid == None:
      print_all_balance(uid)
    else:
      await ctx.send("Not valid command. Use $debug help to get list of commands")
  elif len(args) == 4:
    uid = get_user_from_at(args[2])
    if args[0] == "balance" and args[1] == "delete" and not uid == None:
      print(delete_balance_id(uid, args[3]))
  elif len(args) == 5:
    uid = get_user_from_at(args[2])
    if args[0] == "balance" and args[1] == "rename" and not uid == None:
      print(rename_balance_id(uid, args[3], args[4]))
  else:
    await ctx.send("Not valid command. Use $debug help to get list of commands")

# debug command
@bot.command()
async def reset_bet_winners_to_match_winners(ctx):
  return
  bets = get_all_objects("bet")
  for bet in bets:
    if not int(get_from_list("match", bet.match_id).winner) == 0:
      bet.winner = int(get_from_list("match", bet.match_id).winner)
      replace_in_list("bet", bet.code, bet)
      await ctx.send(embed=await create_bet_embedded(bet))


# debug command
@bot.command()
async def round_all_user_balances(ctx):
  return
  users = get_all_objects("user")
  for user in users:
    for bal in user.balance:

      user.balance[user.balance.index(bal)] = (user.balance[user.balance.index(bal)][0], round(user.balance[user.balance.index(bal)][1], 5), user.balance[user.balance.index(bal)][2])

    replace_in_list("user", user.code, user)


# debug command
@bot.command()
async def delete_last_bal(ctx):
  return
  users = get_all_objects("user")
  for user in users:
    print(user.balance)
    if type(user.balance[-1][1]) == tuple:
      user.balance.pop()
      print(user.balance)
      replace_in_list("user", user.code, user)


# debug command
@bot.command()
async def add_var(ctx):
  matches = get_all_objects("match")
  for match in matches:
    match.date_winner = match.date_closed
    replace_in_list("match", match.code, match)

# debug command
@bot.command()
async def test_get_object(ctx):
  user = get_from_list("user", ctx.author.id)
  replace_in_list("user", user.code, user)
  print("done")

@bot.command()
async def find_common_ids(ctx):
  matches = get_all_objects("match")
  bets = get_all_objects("bet")
  
  
  match_copies = [item for item, count in collections.Counter(matches).items() if count > 1]
  bet_copies = [item for item, count in collections.Counter(bets).items() if count > 1]
  await ctx.send(f"match copies {match_copies}, bet copies {bet_copies}")
  
# debug command
@bot.command()
async def update_bet_ids(ctx):
  return
  users = get_all_objects("user")
  for user in users:
    for bal in user.balance:
      if user.balance[user.balance.index(bal)][0] == "reset 1":
        user.balance[user.balance.index(bal)] = ("reset_2022 Stage 1" , user.balance[user.balance.index(bal)][1], user.balance[user.balance.index(bal)][2])

    replace_in_list("user", user.code, user)


keep_alive()
bot.run(os.getenv("TOKEN"))