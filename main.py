
# add moddifacation when no on incorrect match creation
# rename, remove, get all balance_id
# double check balance rounding
# test bet list with and without await
# have it replace by code not by value
# test prefix unique with 1 long in test code


from keepalive import keep_alive

from io import BytesIO
import collections
import discord
from discord.commands import Option,OptionChoice , SlashCommandGroup
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

print(discord.__version__)
intents = discord.Intents.default()
intents.members = True

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
      match_t_list.append((f"{match.t1} vs {match.t2}".lower(), match.code))
  return match_t_list

async def avalable_bets_name_code(bot):
  matches = get_all_objects("match")
  bet_list = []
  for match in matches:
    if match.date_closed is None:
      for bet_id in match.bet_ids:
        bet = get_from_list("bet", bet_id)
        name = (await smart_get_user(bet.user_id, bot)).display_name
        bet_list.append(OptionChoice(name=f"{name} {bet.amount} on {bet.get_team(match)}", value=bet.code))
  return bet_list


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
  # to do, update everything ahead

  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return "User not found"
  indices = [i for i, x in enumerate(user.balance) if x[0] == balance_id]
  if len(indices) > 1:
    print("More than one balance_id found")
  elif len(indices) == 0:
    return "No balance_id found"
  #to do
  #reset_range = self.get_reset_range(indices[0])
  #index = indices[0] + 1
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
      print("no msg found")


def is_key(key):
  keys = db.keys()
  return key in keys


def is_digit(str):
  try:
    int(str)
    return True
  except ValueError:
    return False


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
    embed.add_field(name="Betting Closed:", value="No", inline=True)
  else:
    closed_date_formatted = match.date_closed.strftime("%m/%d/%Y at %H:%M:%S")
    embed.add_field(name="Betting Closed:", value=closed_date_formatted, inline=True)

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


def add_to_active_ids(user_ambig, bet_id):
  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return None

  user.active_bet_ids.append(bet_id)
  replace_in_list("user", user.code, user)


def remove_from_active_ids(user_ambig, bet_id):
  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return None

  if not bet_id in user.active_bet_ids:
    print("Bet_id Not Found")
    return
  user.active_bet_ids.remove(bet_id)
  print(replace_in_list("user", user.code, user))


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
  
  
  


async def cancel_match():
  keys = db.keys()
  db["stage"] = 0
  if "current_user" in keys:
    del db["current_user"]
  if "current_t1_name" in keys:
    del db["current_t1_name"]
  if "current_t2_name" in keys:
    del db["current_t2_name"]
  if "current_old_t1_odds" in keys:
    del db["current_old_t1_odds"]
  if "current_old_t2_odds" in keys:
    del db["current_old_t2_odds"]
  if "current_t1_odds" in keys:
    del db["current_t1_odds"]
  if "current_t2_odds" in keys:
    del db["current_t2_odds"]
  if "tournament_name" in keys:
    del db["tournament_name"]
  if "current_match" in keys:
    del db["current_match"]


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

  print(" ")
  print(message.author)
  print(message.content)
  await bot.process_commands(message)

  # hard reset but logs and channel ids
  if message.content == "$clear the database of bad keys please and thank you":
    return
    all_keys = db.keys()
    keys = []
    for k in all_keys:
      if not (k.startswith("log_") or k.endswith("_channel_id")):
        keys.append(k)

    db["log_" + get_uniqe_code("log")] = jsonpickle.encode(("a little called " + message.author.name + " ID: " + str(message.author.id) + " cleared database \nkeys include " + str(keys)), datetime.now())

    for k in keys:
      del db[k]
    await message.channel.send("Good Bye World")

    return

  if message.content.startswith("$"):
    return

  if message.channel.id == db["creation_channel_id"]:
    # match creator
    if not "stage" in db.keys():
      db["stage"] = 0

    stage = db["stage"]

    if stage >= 0:
      if stage == 1:
        if message.author.id == db["current_user"]:

          db["current_t1_name"] = message.content
          await message.channel.send("What is Team 2's Name")

          db["stage"] = 2

      elif stage == 2:
        if message.author.id == db["current_user"]:

          db["current_t2_name"] = message.content
          await message.channel.send("What is Team 1's Odds\nEnter in the amount you would get if you bet 1")

          db["stage"] = 3

      elif stage == 3:
        if message.author.id == db["current_user"]:
          s = message.content
          stemp = s.replace(".", "")
          if is_digit(stemp) and (s.find(".") == -1 or s.find(".") == 1):
            await message.channel.send("What is Team 2's Odds\nEnter in the amount you would get if you bet 1")

            db["current_old_t1_odds"] = float(s)
            db["stage"] = 4
          else:
            await message.channel.send("Please enter a valid number")

      elif stage == 4:
        if message.author.id == db["current_user"]:
          s = message.content
          stemp = s.replace(".", "")

          if is_digit(stemp) and (s.find(".") == -1 or s.find(".") == 1):
            await message.channel.send("Do you want to balance the odds?")

            db["current_old_t2_odds"] = float(s)
            db["stage"] = 5
          else:
            await message.channel.send("Please enter a valid number")

      elif stage == 5:
        if message.author.id == db["current_user"]:

          if message.content.lower() == "yes":
            odds1 = db["current_old_t1_odds"]
            odds2 = db["current_old_t2_odds"]

            odds1 = 1 / odds1
            odds2 = 1 / odds2

            percentage1 = odds1 / (odds1 + odds2)
            percentage2 = odds2 / (odds1 + odds2)

            odds1 = 1 / percentage1
            odds2 = 1 / percentage2

            db["current_t1_odds"] = roundup(odds1)
            db["current_t2_odds"] = roundup(odds2)

            await message.channel.send("The new odds are " + str(db["current_t1_odds"]) + " / " + str(db["current_t2_odds"]) + "\nWhat is the Tournament Name")

            db["stage"] = 6
          elif message.content.lower() == "no":
            await message.channel.send("What is the Tournament Name")

            db["current_t1_odds"] = db["current_old_t1_odds"]
            db["current_t2_odds"] = db["current_old_t2_odds"]
            db["stage"] = 6
          else:
            await message.channel.send("Please enter either yes or no")

      elif stage == 6:
        if message.author.id == db["current_user"]:

          db["tournament_name"] = message.content
          await message.channel.send("Where are the odds from")

          db["stage"] = 7

      elif stage == 7:
        if message.author.id == db["current_user"]:

          odds_source = message.content

          code = str(get_uniqe_code("match"))

          t1n = db["current_t1_name"]
          t2n = db["current_t2_name"]
          t1oo = db["current_old_t1_odds"]
          t2oo = db["current_old_t2_odds"]
          t1o = db["current_t1_odds"]
          t2o = db["current_t2_odds"]
          tn = db["tournament_name"]

          cmatch = Match(t1n, t2n, t1oo, t2oo, t1o, t2o, tn, odds_source, message.author.id, datetime.today(), code)

          db["current_match"] = jsonpickle.encode(cmatch)
          print(jsonpickle.encode(cmatch))

          s = "Is this right?\n"
          date_formatted = cmatch.date_created.strftime("%m/%d/%Y %H:%M:%S")
          s += "Teams: " + str(cmatch.t1) + " vs " + str(cmatch.t2) + "\nOdds: " + str(cmatch.t1o) + " / " + str(cmatch.t2o) + "\nTournament Name: " + str(cmatch.tournament_name) + "\nOdds Source: " + str(cmatch.odds_source) + "\nCreator: " + str((await smart_get_user(cmatch.creator, bot)).mention) + "\nCreated On: " + str(date_formatted)

          await message.channel.send(s, allowed_mentions=discord.AllowedMentions(users=False))

          db["stage"] = 8
      elif stage == 8:
        if message.author.id == db["current_user"]:

          if message.content.lower() == "yes":
            cmatch = jsonpickle.decode(db["current_match"])
            embedd = await create_match_embedded(cmatch)
            msg = await (await bot.fetch_channel(db["match_channel_id"])).send(embed=embedd)
            cmatch.message_ids.append((msg.id, msg.channel.id))
            add_to_list("match", cmatch)

            await message.channel.send("Match Created")
            await cancel_match()

          elif message.content.lower() == "no":
            # to do add moddifacation
            await message.channel.send("Cancelled")
            await cancel_match()

          else:
            await message.channel.send("Please enter either yes or no")


# create match command
@bot.command()
async def match(ctx, *args):

  if len(args) == 0:
    # match creator
    if ctx.channel.id == db["creation_channel_id"]:
      await cancel_match()

      await ctx.send("What is Team 1's Name")

      db["current_user"] = ctx.author.id
      db["stage"] = 1
    else:
      channel = await bot.fetch_channel(db["creation_channel_id"])
      await ctx.send("Please put command in " + str(channel.mention))
  elif len(args) == 1:
    if args[0] == "help":
      await ctx.send(
        """$match: starts match creation
$match cancel: cancels match creation
$match [Identifier]: replaces message with match info
$match close betting [Identifier]: closes betting
$match open betting [Identifier]: open betting
$match winner [Identifier] [team]: sets the team's winner and pays out all bets, (to do): if winner is already set it takes back on all bets (a team of 0 sets the team to none)
$match winner override [Identifier] [team]: switches the team's winner and updates payout on \ all bets, (to do): if winner is already set it takes back on all bets (a team of 0 sets the team to none)
$match delete [Identifier]: deletes match along with all bets connected, can only be done before payout
$match list: sends a shorter embed of all matches without a winner
$match list new: sends a shorter embed of all matches that you havent bet on without a winner
$match list full: sends embed of all matches without a winner"""
      )

    elif args[0] == "list":
      matches = get_all_objects("match")
      match_list = []
      for match in matches:
        if int(match.winner) == 0:
          match_list.append(match)
      if len(match_list) == 0:
        await ctx.send("No undecided matches.")
        return

      embedd = await create_match_list_embedded("Matches:", match_list)
      await ctx.send(embed=embedd)

    elif args[0] == "cancel":
      await cancel_match()
      await ctx.send("Cancelled")

    elif len(args[0]) == 8:
      match = get_from_list("match", args[0])
      if match == None:
        await ctx.send("Identifier Not Found")
        return
      embedd = await create_match_embedded(match)
      msg = await ctx.send(embed=embedd)
      match.message_ids.append((msg.id, msg.channel.id))
      replace_in_list("match", match.code, match)
      await ctx.message.delete()

    else:
      await ctx.send("Not valid command. Use $match help to get list of commands")

  elif len(args) == 2:
    if args[0] == "delete" and len(args[1]) == 8:
      match = get_from_list("match", args[1])
      if match == None:
        await ctx.send("Identifier Not Found")
        return
      for bet_id in match.bet_ids:
        bet = get_from_list("bet", bet_id)
        for msg_id in bet.message_ids:
          try:
            channel = await bot.fetch_channel(msg_id[1])
            msg = await channel.fetch_message(msg_id[0])
            await msg.delete()
          except Exception:
            print("no msg found")
        remove_from_active_ids(bet.user_id, bet.code)
        remove_from_list("bet", bet_id)

      for msg_id in get_from_list("match", match.code).message_ids:
        try:
          channel = await bot.fetch_channel(msg_id[1])
          msg = await channel.fetch_message(msg_id[0])
          await msg.delete()
        except Exception:
          print("no msg found")
      await ctx.send(remove_from_list("match", args[1]))

    elif args[0] == "list" and args[1] == "new":
      matches = get_all_objects("match")
      match_list = []
      user = get_from_list("user", ctx.author.id)
      for match in matches:
        if int(match.winner) == 0 and (set(user.active_bet_ids).isdisjoint(match.bet_ids)):
          match_list.append(match)
      if len(match_list) == 0:
        await ctx.send("No undecided matches.")
        return

      embedd = await create_match_list_embedded(f"{(await smart_get_user(user.code, bot)).display_name}'s Match:", match_list)
      await ctx.send(embed=embedd)

    elif args[0] == "list" and args[1] == "full":
      matches = get_all_objects("match")
      match_list = []
      for match in matches:
        if int(match.winner) == 0:
          match_list.append(match)
      if len(match_list) == 0:
        await ctx.send("No undecided match.")
      for match in match_list:
        embedd = await create_match_embedded(match)
        if embedd == None:
          await ctx.send("Identifier Not Found")
          return
        msg = await ctx.send(embed=embedd)
        match.message_ids.append((msg.id, msg.channel.id))
        replace_in_list("match", match.code, match)

    else:
      await ctx.send("Not valid command. Use $match help to get list of commands")

  elif len(args) == 3:
    if args[0] == "close" and args[1] == "betting" and len(args[2]) == 8:
      match = get_from_list("match", args[2])
      if match == None:
        await ctx.send("Identifier Not Found")
        return
      match.date_closed = datetime.now()
      replace_in_list("match", match.code, match)
      embedd = await create_match_embedded(match)
      await edit_all_messages(match.message_ids, embedd)

      await ctx.send("Betting Closed")

    elif args[0] == "open" and args[1] == "betting" and len(args[2]) == 8:
      match = get_from_list("match", args[2])
      if match == None:
        await ctx.send("Identifier Not Found")
        return
      match.date_closed = None
      replace_in_list("match", match.code, match)
      embedd = await create_match_embedded(match)
      await edit_all_messages(match.message_ids, embedd)
      await ctx.send("Betting Opened")

    elif args[0].startswith("winner") and len(args[1]) == 8 and (args[2] == str(1) or args[2] == str(2)):
      match = get_from_list("match", args[1])
      if match == None:
        await ctx.send("Identifier Not Found")
        return
      if int(match.winner) == 0 or args[0] == "winnerforce":
        match.winner = int(args[2])
        match.date_closed = datetime.now()
        replace_in_list("match", match.code, match)
        embedd = await create_match_embedded(match)
        await edit_all_messages(match.message_ids, embedd)
        odds = 0.0
        if int(args[2]) == 1:
          odds = match.t1o
          await ctx.send("Winner has been set to " + match.t1)
        else:
          odds = match.t2o
          await ctx.send("Winner has been set to " + match.t2)

        msg_ids = []
        users = []
        date = datetime.now()
        for bet_id in match.bet_ids:
          bet = get_from_list("bet", bet_id)
          if not bet == None:
            bet.winner = int(match.winner)
            payout = -bet.bet_amount
            if bet.team_num == int(args[2]):
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

      else:
        # to do change winner
        await ctx.send("Winner already set")

    else:
      await ctx.send("Not valid command. Use $match help to get list of commands")

  elif len(args) == 4:
    
    if args[0].startswith("winner") and args[1].startswith("override") and len(args[2]) == 8 and (args[3] == str(1) or args[3] == str(2)):
      match = get_from_list("match", args[2])
      if match == None:
        await ctx.send("Identifier Not Found")
        return
        
      if match.winner == int(args[3]):
        await ctx.send("Winner is already set to that.")
        return

      if not (match.winner == 1 or match.winner == 2):
        await ctx.send("Winner has not been set yet")
        return

      
      match.winner = int(args[3])
      replace_in_list("match", match.code, match)
      embedd = await create_match_embedded(match)
      await edit_all_messages(match.message_ids, embedd)
      msg_ids = []
      for bet_id in match.bet_ids:
        bet = get_from_list("bet", bet_id)
        user = get_from_list("user", bet.user_id)

        balance_id = "id_" + bet.code
        index = [x for x, y in enumerate(user.balance) if y[0] == str(balance_id)]
        
        if not len(index) == 1:
          print(str(len(index)) + " copy of id")
          return None
        if int(args[3]) == bet.team_num:
          payout = bet.get_team_and_payout()[1]
        else:
          payout = -bet.bet_amount
          
        index = index[0]
        new_amount = user.balance[index-1][1] + payout

        replace_in_list("user", user.code, change_prev_balance(user, balance_id, new_amount))

        bet.winner = int(match.winner)
        replace_in_list("bet", bet.code, bet)
        embedd = await create_bet_embedded(bet)
        msg_ids.append((bet.message_ids, embedd))
      
      [await edit_all_messages(tup[0], tup[1]) for tup in msg_ids]
      await ctx.send("Updated winner") 
        
    else:
      await ctx.send("Not valid command. Use $match help to get list of commands")    
  else:
    await ctx.send("Not valid command. Use $match help to get list of commands")


# create bet command
@bot.command()
async def bet(ctx, *args):

  if len(args) == 1:
    arg = args[0]
    if arg == "help":
      await ctx.send(
        """$bet [match id] [team] [amount]: you make a bet on the match with match id on the team ("1" for first team listed "2" for second team listed) amount is whole numbers only
$bet cancel [bet id]: removes bet if bets are still open
$bet [bet id]: replaces your command with bet info
$bet list: sends embed with all bets without a winner
$bet list full: sends embeds of all bets without a winner
$bet winner [bet id]: sets the bets winner (should mostly only be used after an error)"""
      )

    elif args[0] == "list":
      bets = get_all_objects("bet")
      bet_list = []
      for bet in bets:
        if int(bet.winner) == 0:
          bet_list.append(bet)
      if len(bet_list) == 0:
        await ctx.send("No undecided bets.")
        return
      gen_msg = await ctx.send("Generating list...")
      embedd = await create_bet_list_embedded("Bets:", bet_list)
      await ctx.send(embed=embedd)
      await gen_msg.delete()

    elif len(arg) == 8:
      bet = get_from_list("bet", arg)
      if bet == None:
        await ctx.send("Identifier Not Found")
        return
      embedd = await create_bet_embedded(bet)
      msg = await ctx.send(embed=embedd)
      bet.message_ids.append((msg.id, msg.channel.id))
      replace_in_list("bet", bet.code, bet)
      await ctx.message.delete()
    else:
      await ctx.send("Not valid command. Use $bet help to get list of commands")

  elif len(args) == 2:

    if args[0] == "list" and args[1] == "full":
      bets = get_all_objects("bet")
      bet_list = []
      for bet in bets:
        if int(bet.winner) == 0:
          bet_list.append(bet)
      if len(bet_list) == 0:
        await ctx.send("No undecided bets.")
      for bet in bet_list:
        embedd = await create_bet_embedded(bet)
        if embedd == None:
          await ctx.send("Identifier Not Found")
          return
        msg = await ctx.send(embed=embedd)
        bet.message_ids.append((msg.id, msg.channel.id))
        replace_in_list("bet", bet.code, bet)

    elif args[0].startswith("cancel") and len(args[1]) == 8:
      bet = get_from_list("bet", args[1])
      if bet == None:
        await ctx.send("Identifier Not Found")
        return
      match = get_from_list("match", bet.match_id)

      if args[0] == "cancelforce" or match == None or match.date_closed == None:
        if not match == None:
          try:
            match.bet_ids.remove(bet.code)
            replace_in_list("match", match.code, match)
            embedd = await create_match_embedded(match)
            await edit_all_messages(match.message_ids, embedd)
          except:
            print(f"{bet.code} is not in match {match.code} bet ids {match.bet_ids}")
          

        for msg_id in bet.message_ids:
          try:
            channel = await bot.fetch_channel(msg_id[1])
            msg = await channel.fetch_message(msg_id[0])

            await msg.delete()
          except Exception:
            print("no msg found")
        remove_from_active_ids(bet.user_id, bet.code)
        await ctx.send(remove_from_list("bet", args[1]))

      else:
        await ctx.send("Match betting has closed cannot bet")
    else:
      await ctx.send("Not valid command. Use $bet help to get list of commands")

  elif len(args) == 3:
    match_id, team_num, amount = args
    if args[0].startswith("winner") and len(args[1]) == 8 and len(args[2]) == 1 and is_digit(args[2]):
      bet = get_from_list("bet", args[1])
      if bet == None:
        await ctx.send("Identifier Not Found")
        return

      match = get_from_list("match", bet.match_id)
      if int(bet.winner) == 0 or args[0] == "winnerforce":
        bet.winner = int(args[2])
        if int(args[2]) == 1:
          odds = match.t1o
          await ctx.send("Winner has been set to " + match.t1)
        else:
          odds = match.t2o
          await ctx.send("Winner has been set to " + match.t2)

        payout = -bet.bet_amount
        if bet.team_num == int(args[2]):
          payout += bet.bet_amount * odds
        user = get_from_list("user", bet.user_id)
        remove_from_active_ids(user, bet.code)
        add_balance_user(user, payout, "id_" + str(bet.code))

        replace_in_list("bet", bet.code, bet)
        embedd = await create_bet_embedded(bet)
        await edit_all_messages(bet.message_ids, embedd)

        embedd = await create_user_embedded(user)
        await ctx.send(embed=embedd)
      return

    # $bet [match id] [team_num] [amount]
    if not is_digit(amount):
      await ctx.send("Not valid command. Use $bet help to get list of commands")
      return
    
    if not (int(team_num) == 1 or int(team_num) == 2):
      await ctx.send("Team num has to either be 1 or 2")
      return

    if int(amount) <= 0:
      await ctx.send("Cant bet negatives")
      return
    match = get_from_list("match", match_id)
    if match == None:
      await ctx.send("Identifier Not Found")
      return

    if not match.date_closed == None:
      await ctx.send("Betting has closed you cannot make a bet.")
      return

    code = get_uniqe_code("bet")
    user = get_from_list("user", ctx.author.id)
    if user == None:
      user = create_user(ctx.author.id)

    balance_left = user.get_balance() - int(amount)
    if balance_left < 0:
      if int(amount) <= 100:
        await ctx.send("You have bet " + str(math.floor(-balance_left)) + " more than you have, try taking out a loan")
        return
      await ctx.send("You have bet " + str(math.floor(-balance_left)) + " more than you have")
      return

    bet = Bet(code, match_id, ctx.author.id, int(amount), int(team_num), datetime.now())

    match.bet_ids.append(bet.code)
    add_to_list("bet", bet)
    add_to_active_ids(ctx.author.id, bet.code)

    embedd = await create_bet_embedded(bet)
    channel = await bot.fetch_channel(db["bet_channel_id"])
    msg = await channel.send(embed=embedd)

    bet.message_ids.append((msg.id, msg.channel.id))
    replace_in_list("match", match.code, match)
    replace_in_list("bet", bet.code, bet)
    if ctx.channel.id == db["bet_channel_id"] or ctx.channel.id == db["match_channel_id"]:
      await ctx.message.delete()
    else:
      await ctx.send("Bet created")
    embedd = await create_match_embedded(match)
    await edit_all_messages(match.message_ids, embedd)

  else:
    await ctx.send("""Not valid command. Use $bet help to get list of commands.
if you want to make a bet do $bet [match id] [team] [amount]""")


  
#bet start
bet = SlashCommandGroup(
  name = "bet", 
  description = "Assigns the discord channel it is put in to that channel type.",
  guild_ids = gid,
)

#bet modal start
class BetModal(Modal):
  
  def __init__(self, match: Match, user: User, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.match = match
    self.user = user
    
    self.add_item(InputText(label=f"{match.t1} vs {match.t2}. Odds: {match.t1o} / {match.t2o}", placeholder=f"1 for {match.t1} and 2 for {match.t2}.", min_length=1, max_length=1))

    self.add_item(InputText(label="Amount you want to bet.", placeholder=f"Your avalable balance is {round(user.get_balance())}.", min_length=1, max_length=20))

  async def callback(self, interaction: discord.Interaction):
    
    match = self.match
    user = self.user
    team_num = self.children[0].value
    amount = self.children[1].value
    
    if not is_digit(amount):
      await interaction.response.send_message("Not valid command. Use $bet help to get list of commands.")
      return
    
    if not (int(team_num) == 1 or int(team_num) == 2):
      await interaction.response.send_message("Team num has to either be 1 or 2.")
      return

    if int(amount) <= 0:
      await interaction.response.send_message("Cant bet negatives.")
      return

    if not match.date_closed == None:
      await interaction.response.send_message("Betting has closed you cannot make a bet.")
      return

    code = get_uniqe_code("bet")

    balance_left = user.get_balance() - int(amount)
    if balance_left < 0:
      if int(amount) <= 100:
        await interaction.response.send_message("You have bet " + str(math.floor(-balance_left)) + " more than you have, try taking out a loan.")
        return
      await interaction.response.send_message("You have bet " + str(math.floor(-balance_left)) + " more than you have.")
      return

    bet = Bet(code, match.code, user.code, int(amount), int(team_num), datetime.now())

    match.bet_ids.append(bet.code)
    add_to_list("bet", bet)
    add_to_active_ids(user.code, bet.code)

    embedd = await create_bet_embedded(bet)
    print(embedd)
    channel = await bot.fetch_channel(db["bet_channel_id"])
    msg = await interaction.response.send_message(embed=embedd)

    bet.message_ids.append((msg.id, msg.channel.id))
    replace_in_list("match", match.code, match)
    replace_in_list("bet", bet.code, bet)
    embedd = await create_match_embedded(match)
    await edit_all_messages(match.message_ids, embedd)
#bet modal end

  
#bet autocomplete start
async def bet_list_ac(ctx: discord.AutocompleteContext):
  
  match_t_list = avalable_matches_name_code()
  return [match_t[0] for match_t in match_t_list if ctx.value.lower() in match_t[0]]
#bet autocomplete end
      

#bet create start
@bet.command(name = "create", description = "Create a bet.")
async def bet_create(ctx, match: Option(str, "Match you want to bet on.",  autocomplete=bet_list_ac)):
  
  user = get_from_list("user", ctx.author.id)
  if user == None:
    create_user(ctx.author.id)
    
  match_t_list = avalable_matches_name_code()
  
  match_t = next((match_t for match_t in match_t_list if match == match_t[0]), None)
  if match_t is None:
    match_id = match
  else:
    match_id = match_t[1]

  if (match := get_from_list("match", match_id)) is None:
    await ctx.respond("Match ID not found.")
    return
    
  if match.date_closed is not None:
    await ctx.respond("Betting has closed.")
    
  modal = BetModal(match=match, user=user, title="Create Bet")
  await ctx.interaction.response.send_modal(modal)

#bet create end


#bet cancel start

@bet.command(name = "cancel", description = "Cancels a bet if betting is open on the match.")
async def bet_cancel(ctx, bet = Option(str, "Bet you want to cancel.")):
  
  bet = get_from_list("bet", bet)
  if bet == None:
    await ctx.respond("Identifier not found.")
    return
    
  match = get_from_list("match", bet.match_id)
  if (match is None) or (match.date_closed is not None):
    await ctx.respond("Match betting has closed, you cannot cancel the bet.")
    return
    
  gen_msg = await ctx.respond("Deleting bet...")
    
  try:
    match.bet_ids.remove(bet.code)
    replace_in_list("match", match.code, match)
    embedd = await create_match_embedded(match)
    await edit_all_messages(match.message_ids, embedd)
  except:
    print(f"{bet.code} is not in match {match.code} bet ids {match.bet_ids}")
    
  for msg_id in bet.message_ids:
    try:
      channel = await bot.fetch_channel(msg_id[1])
      msg = await channel.fetch_message(msg_id[0])

      await msg.delete()
    except Exception:
      print("no msg found")
  remove_from_active_ids(bet.user_id, bet.code)
  await gen_msg.edit_original_message(remove_from_list("bet", bet.code))
#bet cancel end


#bet find start
@bet.command(name = "find", description = "Sends the embed of the bet.")
async def bet_find(ctx):
  print("find")
#bet find end


#bet list start
@bet.command(name = "list", description = "sends embed with all bets. If type is full it sends the whole embed.")
async def bet_list(ctx):
  print("list")
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
  return
  users = get_all_objects("user")
  for user in users:
    user.loans = []
    replace_in_list("user", user.code, user)

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
    print(user.active_bet_ids)
    for bal in user.balance:
      if user.balance[user.balance.index(bal)][0] == "reset 1":
        user.balance[user.balance.index(bal)] = ("reset_2022 Stage 1" , user.balance[user.balance.index(bal)][1], user.balance[user.balance.index(bal)][2])

    replace_in_list("user", user.code, user)


keep_alive()
bot.run(os.getenv("TOKEN"))
