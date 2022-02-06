# add moddifacation when no on incorrect match creation
# rename, remove, get all balance_id
# double check balance rounding
# test bet list with and without await

from keepalive import keep_alive

import discord
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

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(intents=intents, command_prefix="$")

# matches are in match_list_[identifier] one key contains 50 matches, indentifyer incrimentaly counts up
# user is in user_list_[identifier] one key contains 50 users, indentifyer incrimentaly counts up
# bet is in bet_list_[identifier] one key contains 50 users, indentifyer incrimentaly counts up
# logs are log_[ID] holds (log, date)


def ambig_to_obj(ambig, prefix):
  if isinstance(ambig, int) or isinstance(ambig, str):
    obj = get_from_list(prefix, ambig)
  else:
    obj = ambig
  if obj == None:
    return None
  return obj


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
  if len(indices) > 10:
    return "More than one balance_id found"
  elif len(indices) == 0:
    return "No balance_id found"
  else:
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
    except Exception as e:
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
  codes = [k.code for k in all_objs]
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
  embed.add_field(name="Name:", value=(await smart_get_user(user.code, bot)).mention, inline=True)
  embed.add_field(name="Balance:", value=math.floor(user.balance[-1][1]), inline=True)
  embed.add_field(name="Balance Available:", value=math.floor(user.balance[-1][1] - user.available()), inline=True)
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


def add_balance_user(user_ambig, change, description):
  user = ambig_to_obj(user_ambig, "user")
  if user == None:
    return None

  user.balance.append((description, round(user.balance[-1][1] + change, 5), datetime.now()))
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
          except Exception as e:
            print("no msg found")
        remove_from_active_ids(bet.user_id, bet.code)
        remove_from_list("bet", bet_id)

      for msg_id in get_from_list("match", match.code).message_ids:
        try:
          channel = await bot.fetch_channel(msg_id[1])
          msg = await channel.fetch_message(msg_id[0])
          await msg.delete()
        except Exception as e:
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
        for bet_id in match.bet_ids:
          bet = get_from_list("bet", bet_id)
          if not bet == None:
            bet.winner = int(match.winner)
            payout = -bet.bet_amount
            if bet.team_num == int(args[2]):
              payout += bet.bet_amount * odds
            user = get_from_list("user", bet.user_id)
            remove_from_active_ids(user, bet.code)
            add_balance_user(user, payout, "id_" + str(bet.code))

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
      if match.date_closed == None or args[0] == "cancelforce":
        match.bet_ids.remove(bet.code)
        replace_in_list("match", match.code, match)
        embedd = await create_match_embedded(match)
        await edit_all_messages(match.message_ids, embedd)

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
    if not is_digit(amount) and (team_num == 1 or team_num == 2):
      await ctx.send("Not valid command. Use $bet help to get list of commands")
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

    balance_left = user.balance[-1][1] - int(amount) - user.available()
    if balance_left < 0:
      await ctx.send("You have bet " + str(math.floor(-balance_left)) + " more than you have")
      return

    bet = Bet(code, match_id, ctx.author.id, int(amount), int(team_num), datetime.now())

    match.bet_ids.append(bet.code)
    replace_in_list("match", match.code, match)
    embedd = await create_match_embedded(match)
    add_to_list("bet", bet)
    add_to_active_ids(ctx.author.id, bet.code)
    embedd = await create_bet_embedded(bet)
    msg = await (await bot.fetch_channel(db["bet_channel_id"])).send(embed=embedd)

    await edit_all_messages(bet.message_ids, embedd)
    bet.message_ids.append((msg.id, msg.channel.id))
    replace_in_list("bet", bet.code, bet)
    if ctx.channel.id == db["bet_channel_id"] or ctx.channel.id == db["match_channel_id"]:
      await ctx.message.delete()
    else:
      await ctx.send("bet created")
    await edit_all_messages(match.message_ids, embedd)

  else:
    await ctx.send("Not valid command. Use $bet help to get list of commands")


# debug
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
$debug balance rename [user @] "old balance id" "new balance id": replaces balance ID with new ID"""
      )

    elif args[0] == "keys":
      await ctx.send(str(db.keys())[1:-1])

    else:
      await ctx.send("Not valid command. Use $debug help to get list of commands")

  elif len(args) == 2:

    if args[0] == "list" and (args[1] == "match" or args[1] == "user" or args[1] == "bet"):
      objects = get_all_objects(args[1])
      output = ""
      for obj in objects:
        output += obj.to_string() + "\n"
      if not output == "":
        await ctx.send(output)
      else:
        await ctx.send("No keys of type " + args[1])

    elif args[0] == "key":
      print(str(db[args[1]]))

    else:
      await ctx.send("Not valid command. Use $debug help to get list of commands")

  elif len(args) == 3:
    uid = args[2].replace("<", "")
    uid = uid.replace(">", "")
    uid = uid.replace("@", "")
    uid = uid.replace("!", "")
    if args[0] == "reassign":
      db[args[2]] = db[args[1]]
      del db[args[1]]
      await ctx.send("key " + args[1] + " is now " + args[2])

    elif args[0] == "delete" and args[1] == "key":
      del db[args[2]]
      await ctx.send("deleted " + str(args[2]))

    elif args[0] == "balance" and args[1] == "print" and is_digit(uid):
      print_all_balance(uid)
    else:
      await ctx.send("Not valid command. Use $debug help to get list of commands")
  elif len(args) == 4:
    uid = args[2].replace("<", "")
    uid = uid.replace(">", "")
    uid = uid.replace("@", "")
    uid = uid.replace("!", "")
    if args[0] == "balance" and args[1] == "delete" and is_digit(uid):
      print(delete_balance_id(uid, args[3]))
  elif len(args) == 5:
    uid = args[2].replace("<", "")
    uid = uid.replace(">", "")
    uid = uid.replace("@", "")
    uid = uid.replace("!", "")
    if args[0] == "balance" and args[1] == "rename" and is_digit(uid):
      print(rename_balance_id(uid, args[3], args[4]))
  else:
    await ctx.send("Not valid command. Use $debug help to get list of commands")


@bot.command()
async def back(ctx):
  if not db["stage"] == 0:
    db["stage"] = db["stage"] - 1
    print(db["stage"])
    # to do give the text
    await ctx.send("Backed up for you :)")
  else:
    await ctx.send("Backed all the way up")


# assign bot spicific action to channel
@bot.command()
async def assign(ctx, *args):
  if not len(args) == 1:
    await ctx.send("Not a valid command do $assign help for list of commands")
    return
  arg = args[0]
  if arg == "help":
    await ctx.send(
      """$assign creation: where match creation takes place
$assign matches: where the end matches and bets show up
$assign bets: where the end bets show up"""
    )
  elif arg == "creation":
    db["creation_channel_id"] = ctx.channel.id
    await ctx.send("This channel is now the match creation channel")
  elif arg == "matches":
    db["match_channel_id"] = ctx.channel.id
    await ctx.send("This channel is now the match list channel")
  elif arg == "bets":
    db["bet_channel_id"] = ctx.channel.id
    await ctx.send("This channel is now the bet list channel")
  else:
    await ctx.send("Not a valid command do $assign help for list of commands")


# returns your own or someone else's balance
@bot.command()
async def balance(ctx, *args):
  if len(args) == 0:
    user = get_from_list("user", ctx.author.id)
    if user == None:
      create_user(ctx.author.id)
    embedd = await create_user_embedded(user)
    if embedd == None:
      await ctx.send("Identifier Not Found")
      return
    await ctx.send(embed=embedd)

  elif len(args) == 1:
    uid = args[0].replace("<", "")
    uid = uid.replace(">", "")
    uid = uid.replace("@", "")
    uid = uid.replace("!", "")
    if args[0] == "help":
      await ctx.send(
        """$balance gives your own balance
$balance [user's @]: gives balance of that user"""
      )
    elif is_digit(uid):
      embedd = await create_user_embedded(int(uid))
      if embedd == None:
        await ctx.send("Identifier Not Found")
        return
      await ctx.send(embed=embedd)
    else:
      await ctx.send("Not a valid command do $balance help for list of commands")
  else:
    await ctx.send("Not a valid command do $balance help for list of commands")


# gives points
@bot.command()
async def award(ctx, *args):
  if len(args) == 1:
    if args[0] == "help":
      await ctx.send("""$award [user @] [amount] "[description]": adds the amount to the user from the bank, description needs to be in quotes. DON'T USE WITHOUT PERMISSION""")
  elif len(args) == 3:
    uid = args[0].replace("<", "")
    uid = uid.replace(">", "")
    uid = uid.replace("@", "")
    uid = uid.replace("!", "")
    if not (is_digit(uid) and is_digit(args[1])):
      await ctx.send("Not a valid command do $award help for list of commands")
      return

    user = add_balance_user(uid, int(args[1]), "award_" + args[2])
    if user == None:
      await ctx.send("User not found")
    else:
      embedd = await create_user_embedded(user)
      await ctx.send(embed=embedd)

  else:
    await ctx.send("Not a valid command do $award help for list of commands")


# help
bot.remove_command("help")


@bot.command()
async def help(ctx):
  await ctx.send(
    """All commands have their own help. To go to help type $[command] help
$match: startes match setup and lists match
$back: goes backwards in match stage
$bet: creates and lists bet
$assign: assigns what channels do what functions
$balance: returns your own or someone else's balance
$leaderboard: gives leaderboard of balances
$award: addes the money to someone's account DON'T USE WITHOUT PERMISSION""")


@bot.command()
async def leaderboard(ctx, *arg):

  if len(arg) == 0:
    embedd = await create_leaderboard_embedded()
    await ctx.send(embed=embedd)
  elif len(arg) == 1:
    if len(arg) == "help":
      await ctx.send("""$leaderboard: shows a learderboard""")
    else:
      await ctx.send("Not a valid command do $leaderboard help for list of commands")
  else:
    await ctx.send("Not a valid command do $leaderboard help for list of commands")


# season reset command
@bot.command()
async def reset_season(ctx):
  # to do make the command also include season name
  return
  users = get_all_objects("user")
  for user in users:
    user.balance.pop()
    user.balance.append(("reset 2", 500, datetime.now()))
    replace_in_list("user", user.code, user)


# gives 50 if under 100
@bot.command()
async def loan(ctx, *args):
  return
  if len(args) == 0:
    user = get_from_list("user", ctx.author.id)
    if user == None:
      await ctx.send("You do not have an account yet do $balance or make an account to create an account")
    if user.balance[-1][1] < 100:
      loan_amount = len(user.loans)
      loan_price = 50 + loan_amount * 10
      user.loan.append((loan_price, datetime.now, None))
      replace_in_list("user", user.code, user)
    else:
      await ctx.send("You must have less than 100 to make a loan")

  elif len(args) == 1:
    if args[0] == "help":
      await ctx.send("""$loan: gives you 50 and adds a loan that you have to pay (50 + the amount of loans you haven't paid) to close, all loans get auto paid at 1000+ balance, you need less that 100 to get a loan""")
    else:
      await ctx.send("Not a valid command do $loan help for list of commands")
  else:
    await ctx.send("Not a valid command do $loan help for list of commands")
      


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
async def update_bet_ids(ctx):
  return
  users = get_all_objects("user")
  for user in users:
    print(user.active_bet_ids)
    for bal in user.balance:
      if len(user.balance[user.balance.index(bal)][0]) == 8:
        user.balance[user.balance.index(bal)] = (("id_" + str(user.balance[user.balance.index(bal)][0])), user.balance[user.balance.index(bal)][1], user.balance[user.balance.index(bal)][2])

    replace_in_list("user", user.code, user)


keep_alive()
bot.run(os.getenv("TOKEN"))
