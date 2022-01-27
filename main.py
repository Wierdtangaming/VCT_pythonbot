#add moddifacation when no on incorrect match creation


from keepalive import keep_alive

import discord
import os
import random
from replit import db
from Match import Match
from Bet import Bet
from User import User
import jsonpickle
import math
from datetime import datetime
from discord.ext import commands
import emoji

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(intents=intents, command_prefix="$")

#matches are in match_list_[identifier] one key contains 50 matches, indentifyer incrimentaly counts up
#user is in user_list_[identifier] one key contains 50 users, indentifyer incrimentaly counts up
#bet is in bet_list_[identifier] one key contains 50 users, indentifyer incrimentaly counts up
#logs are log_[ID] holds (log, date)


def get_from_list(prefix, identifier):
  objects = get_all_objects(prefix)
  if objects == None or objects.count == 0:
    return None
  for obj in objects:
    if obj.code == identifier:
      return obj

def add_to_list(prefix, obj):
  print(jsonpickle.encode(obj))
  objects = get_all_objects(prefix)
  if len(objects) == 0:
    db[prefix + "_list_1"] = list([jsonpickle.encode(obj)])
    return
  list_num = math.floor(len(objects) / 50)
  list_prog = len(objects) % 50
  if list_prog == 0:
    db[prefix + "_list_" + str(list_num + 1)] = [jsonpickle.encode(obj)]
    return

  list_to_add = list(db[prefix + "_list_" + str(list_num + 1)])
  list_to_add.append(jsonpickle.encode(obj))
  db[prefix + "_list_" + str(list_num + 1)] = list_to_add


def replace_in_list(prefix, identifier, obj):
  objects = get_all_objects(prefix)
  objects_e = [jsonpickle.encode(obj) for obj in objects]

  if get_from_list(prefix, identifier) == None:
    print(prefix + identifier)
    return "No Identifier Found"
    
  object_to_replace = jsonpickle.encode(get_from_list(prefix, identifier))
  index = objects_e.index(object_to_replace)
  list_num = math.floor(index / 50)

  list_to_replace = list(db[prefix + "_list_" + str(list_num + 1)])
  list_to_replace[list_to_replace.index(object_to_replace)] = jsonpickle.encode(obj)
  db[prefix + "_list_" + str(list_num + 1)] = list_to_replace


def remove_from_list(prefix, identifier):
  objects = get_all_objects(prefix)
  objects_e = [jsonpickle.encode(obj) for obj in objects]

  if get_from_list(prefix, identifier) == None:
    return "No Identifier Found"

  object_to_remove = jsonpickle.encode(get_from_list(prefix, identifier))
  if len(objects_e) == 0 or (not object_to_remove in objects_e):
    return "No Identifier Found"
  index = objects_e.index(object_to_remove)
  list_num = math.floor(index / 50)
  list_to_add = list(db[prefix + "_list_" + str(list_num + 1)])
  list_to_add.remove(object_to_remove)
  if len(list_to_add) == 0:
    del db[prefix + "_list_" + str(list_num + 1)]
    return "Removed " + prefix
  
  db[prefix + "_list_" + str(list_num + 1)] = list_to_add
  if list_num + 1 == len(db.prefix(prefix + "_list_")):
    return "Removed " + prefix
  for x in range(list_num + 1, len(list(db.prefix(prefix + "_list_")))):
    list1 = list(db[prefix + "_list_" + str(x)])
    list2 = list(db[prefix + "_list_" + str(x + 1)])
    list1.append(list2[0])
    list2.remove(list2[0])
    db[prefix + "_list_" + str(x)] = list1

    if len(list2) == 0:
      del db[prefix + "_list_" + str(x + 1)]
    else:
      db[prefix + "_list_" + str(x + 1)] = list2

  return "Removed " + prefix


def get_all_objects(prefix):
  list_keys_unordered = db.prefix(prefix + "_list_")
  if len(list_keys_unordered) == 0:
    print("no keys of type " + prefix)
    return []
  list_keys = [str(prefix + "_list_" + str(x + 1)) for x in range(len(list_keys_unordered))]
  lists = [list(db[listt]) for listt in list(list_keys)]
  list_objects = sum(list(lists), [])
  objs = [jsonpickle.decode(obj) for obj in list_objects]
  return objs



async def edit_all_messages(ids, embedd):
  for id in ids:
    try:
      channel = await bot.fetch_channel(id[1])
      msg = await channel.fetch_message(id[0])
      await msg.edit(embed=embedd)
    except Exception as e:
      print("no msg found" + str(e))
    




def is_key(key):
  keys = db.keys()
  return key in keys


def get_uniqe_code(prefix:str):
  full_keys = db.prefix(prefix + "_")
  codes = full_keys[len(prefix) + 1:]
  code = ""
  copy = True
  while(copy):
    copy = False
    
    random.seed()
    code = str(hex(random.randint(0,2**32-1))[2:]).zfill(8)
    for k in codes:
      if k == code:
        copy = True
  return code

def create_user(user_id):
  random.seed()
  color_code = str(hex(random.randint(0,2**32-1))[2:]).zfill(8)
  user = User(user_id, color_code, datetime.now())
  add_to_list("user", user)
  return user

async def create_match_embedded(identifier):
  match = get_from_list("match", identifier)
  print(match)
  if match == None:
    return None
  embed = discord.Embed(title="Match:", color=discord.Color.from_rgb(*tuple(int((match.code[0:8])[i:i+2], 16) for i in (0, 2, 4))))

  embed.add_field(name = "Teams:", value = match.t1 + " vs " + match.t2, inline = True)
  embed.add_field(name = "Odds:", value = str(match.t1o) + " / " + str(match.t2o), inline = True)
  embed.add_field(name = "Tournament Name:", value = match.tournament_name, inline = True)
  embed.add_field(name = "Odds Source:", value = match.odds_source, inline = True)
  embed.add_field(name = "Creator:", value = (await bot.fetch_user(match.creator)).mention, inline = True)
  date_formatted = match.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  embed.add_field(name = "Created On:", value = date_formatted, inline = True)
  if match.date_closed == None:
    embed.add_field(name = "Betting Closed:", value = "No", inline = True)
  else:
    closed_date_formatted = match.date_closed.strftime("%m/%d/%Y at %H:%M:%S")
    embed.add_field(name = "Betting Closed:", value = closed_date_formatted, inline = True)

  if int(match.winner) == 0:
    embed.add_field(name = "Winner:", value = "None", inline = True)
  else:
    winner_team = ""
    if int(match.winner) == 1:
      winner_team = match.t1
    else:
      winner_team = match.t2

    embed.add_field(name = "Winner:", value = winner_team, inline = True)
  
  embed.add_field(name = "Identifier:", value = match.code, inline = False)
  return embed


async def create_match_list_embedded(match_ids):

  embed = discord.Embed(title="Matches:", color=discord.Color.red())

  for match_id in match_ids:
    match =get_from_list("match", match_id)
    embed.add_field(name = "\n" + "Match: " + match.code, value = match.short_to_string() + "\n", inline = False)
  return embed

  
async def create_bet_embedded(identifier):
  bet = get_from_list("bet", identifier)
  if bet == None:
    return None
  embed = discord.Embed(title="Bet:", color=discord.Color.from_rgb(*tuple(int((bet.code[0:8])[i:i+2], 16) for i in (0, 2, 4))))
  embed.add_field(name = "Match Identifier:", value = bet.match_id, inline = True)
  embed.add_field(name = "User:", value = (await bot.fetch_user(bet.user_id)).mention, inline = True)
  embed.add_field(name = "Amount Bet:", value = bet.bet_amount, inline = True)
  match = get_from_list("match", bet.match_id)
  if bet.team_num == 1:
    embed.add_field(name = "Bet on:", value = match.t1, inline = True)
  else:
    embed.add_field(name = "Bet on:", value = match.t2, inline = True)

  if int(bet.winner) == 0:
    embed.add_field(name = "Winner:", value = "None", inline = True)
  else:
    winner_team = ""
    if int(bet.winner) == 1:
      winner_team = match.t1
    else:
      winner_team = match.t2

    embed.add_field(name = "Winner:", value = winner_team, inline = True)
  
  date_formatted = bet.date_created.strftime("%m/%d/%Y at %H:%M:%S")
  embed.add_field(name = "Created On:", value = date_formatted, inline = True)
  embed.add_field(name = "Identifier:", value = bet.code, inline = False)
  return embed


async def create_user_embedded(identifier):
  user = get_from_list("user", identifier)
  if user == None:
    return None
  embed = discord.Embed(title="User:", color=discord.Color.from_rgb(*tuple(int((user.color_code[0:8])[i:i+2], 16) for i in (0, 2, 4))))
  embed.add_field(name = "Name:", value = (await bot.fetch_user(user.code)).mention, inline = True)
  embed.add_field(name = "Balance:", value = user.balance[-1][1], inline = True)
  return embed


async def create_leaderboard_embedded():
  users = get_all_objects("user")
  user_rankings = [(user.code, user.balance[-1][1]) for user in users]
  user_rankings.sort(key=lambda x:x[1])
  user_rankings.reverse()
  embed = discord.Embed(title="Leaderboard:", color=discord.Color.gold())
  medals = [emoji.demojize("🥇"), emoji.demojize("🥈"), emoji.demojize("🥉")]
  rank_num = 1
  for user_rank in user_rankings:
    rank = ""
    if rank_num > len(medals):
      rank = "#" + str(rank_num)
      embed.add_field(name = rank, value = str((await bot.fetch_user(user_rank[0])).mention) + ": " + str(user_rank[1]) , inline = False)
    else:
      rank = emoji.emojize(medals[rank_num - 1])
      embed.add_field(name = rank, value = str((await bot.fetch_user(user_rank[0])).mention) + ": " + str(user_rank[1]), inline = False)
    rank_num += 1
  return embed

def add_to_active_ids(user_id, bet_id):
  user = get_from_list("user", user_id)
  user.active_bet_ids.append(bet_id)
  replace_in_list("user", user_id, user)

def remove_from_active_ids(user_id, bet_id):
  user = get_from_list("user", user_id)
  user.active_bet_ids.remove(bet_id)
  replace_in_list("user", user_id, user)

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


  #hard reset but logs and channel ids
  if message.content == "$clear the database of bad keys please and thank you":
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
    #match creator
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
          stemp = s.replace('.','')
          if (stemp.isdigit() and (s.find('.') == -1 or s.find('.') == 1)):
            await message.channel.send("What is Team 2's Odds\nEnter in the amount you would get if you bet 1")
        

            db["current_old_t1_odds"] = float(s)
            db["stage"] = 4
          else:
            await message.channel.send("Please enter a valid number")



      elif stage == 4:
        if message.author.id == db["current_user"]:
          s = message.content
          stemp = s.replace('.','')

          if (stemp.isdigit() and (s.find('.') == -1 or s.find('.') == 1)):
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


            odds1 = 1/odds1
            odds2 = 1/odds2

            percentage1 = odds1 /(odds1 + odds2)
            percentage2 = odds2 /(odds1 + odds2)

            odds1 = 1/percentage1
            odds2 = 1/percentage2

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
          s += "Teams: " + str(cmatch.t1) + " vs " + str(cmatch.t2) + "\nOdds: " + str(cmatch.t1o) + " / " + str(cmatch.t2o) + "\nTournament Name: " + str(cmatch.tournament_name) + "\nOdds Source: " + str(cmatch.odds_source) + "\nCreator: " + str((await bot.fetch_user(cmatch.creator)).mention) + "\nCreated On: " + str(date_formatted)
        
          await message.channel.send(s, allowed_mentions=discord.AllowedMentions(users=False))
        

          db["stage"] = 8  
      elif stage == 8:
        if message.author.id == db["current_user"]:
          
          if message.content.lower() == "yes":
            cmatch = jsonpickle.decode(db["current_match"])
            add_to_list("match", cmatch)
            embedd = await create_match_embedded(cmatch.code)
            msg = await bot.get_channel(db["match_channel_id"]).send(embed=embedd)
            cmatch.message_ids.append((msg.id, msg.channel.id))
            replace_in_list("match", cmatch.code, cmatch)

            await message.channel.send("Match Created")
            await cancel_match()

          elif message.content.lower() == "no":
            #to do add moddifacation
            await message.channel.send("Cancelled")
            await cancel_match()

          else:
            await message.channel.send("Please enter either yes or no")





#create match command
@bot.command()
async def match(ctx, *args):

  if len(args) == 0:
    #match creator
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
$match [Identifier]: replaces message with match info
$match close betting [Identifier]: closes betting
$match open betting [Identifier]: open betting
$match winner [Identifier] [team]: sets the team's winner and pays out all bets, to do if winner is already set it takes back on all bets (a team of 0 sets the team to none)
$match delete [Identifier]: deletes match along with all bets connected, can only be done before payout
$match full list: sends embed of all matches without a winner""")

    elif args[0] == "list":
      matches = get_all_objects("match")
      match_ids = []
      for match in matches:
        if int(match.winner) == 0:
          match_ids.append(match.code)
      if len(match_ids) == 0:
        await ctx.send("No undecided matches.")
      
      embedd = await create_match_list_embedded(match_ids)
      await ctx.send(embed=embedd)


    elif len(args[0]) == 8:
      embedd = await create_match_embedded(args[0])
      if embedd == None:
        await ctx.send("Identifier Not Found")
        return
      msg = await ctx.send(embed=embedd)
      match = get_from_list("match", args[0])
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
            print("no msg found" + str(e))
        remove_from_active_ids(bet.user_id, bet.code)
        remove_from_list("bet", bet_id)

      for msg_id in get_from_list("match", match.code).message_ids:
        try:
          channel = await bot.fetch_channel(msg_id[1])
          msg = await channel.fetch_message(msg_id[0])
          await msg.delete()
        except Exception as e:
          print("no msg found" + str(e))
      await ctx.send(remove_from_list("match", args[1]))

    elif args[0] == "full" and args[1] == "list":
      matches = get_all_objects("match")
      match_ids = []
      for match in matches:
        if int(match.winner) == 0:
          match_ids.append(match.code)
      if len(match_ids) == 0:
        await ctx.send("No undecided matches.")
      
      for match_id in match_ids:
        embedd = await create_match_embedded(match_id)
        if embedd == None:
          await ctx.send("Identifier Not Found")
          return
        msg = await ctx.send(embed=embedd)
        match = get_from_list("match", match_id)
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
      embedd = await create_match_embedded(match.code)
      await edit_all_messages(match.message_ids, embedd)

      await ctx.send("Betting Closed")
    elif args[0] == "open" and args[1] == "betting" and len(args[2]) == 8:
      match = get_from_list("match", args[2])
      if match == None:
        await ctx.send("Identifier Not Found")
        return
      match.date_closed = None
      replace_in_list("match", match.code, match)
      embedd = await create_match_embedded(match.code)
      await edit_all_messages(match.message_ids, embedd)
      await ctx.send("Betting Opened")
    elif args[0].startswith("winner") and len(args[1]) == 8 and len(args[2]) == 1 and args[2].isdigit():
      match = get_from_list("match", args[1])
      if match == None:
        await ctx.send("Identifier Not Found")
        return
      if int(match.winner) == 0 or args[0] == "winnerforce":
        match.winner = int(args[2])
        match.date_closed = datetime.now()
        replace_in_list("match", match.code, match)
        embedd = await create_match_embedded(match.code)
        await edit_all_messages(match.message_ids, embedd)
        odds = 0.0
        if int(args[2]) == 1:
          odds = match.t1o
          await ctx.send("Winner has been set to " + match.t1)
        else:
          odds = match.t2o
          await ctx.send("Winner has been set to " + match.t2)

        for bet_ids in match.bet_ids:
          bet = get_from_list("bet", bet_ids)
          bet.winner = int(match.winner)
          payout = -bet.bet_amount
          if(bet.team_num == int(args[2])):
            payout += bet.bet_amount * odds
          user = get_from_list("user", bet.user_id)
          remove_from_active_ids(user.code, bet.code)
          user.balance.append((bet.code, round(user.balance[-1][1] + payout, 5), datetime.now()))
          
          
          replace_in_list("bet", bet.code, bet)
          embedd = await create_bet_embedded(bet.code)
          await edit_all_messages(bet.message_ids, embedd)
          replace_in_list("user", user.code, user)

          embedd = await create_user_embedded(user.code)
          await ctx.send(embed=embedd)
        

      else:
        #to do change winner
        await ctx.send("Winner already set")
        

    else:
      await ctx.send("Not valid command. Use $match help to get list of commands")

  else:
    await ctx.send("Not valid command. Use $match help to get list of commands")

  



#create bet command
@bot.command()
async def bet(ctx, *args):

  if len(args) == 1:
    arg = args[0]
    if arg == "help":
      await ctx.send(
      """$bet [match id] [team] [amount]: you make a bet on the match with match id on the team ("1" for first team listed "2" for second team listed) amount is whole numbers only
$bet cancel [bet id]: removes bet if bets are still open
$bet [bet id]: replaces your command with bet info
$bet list: to do sends embed of all bets without a winner""")

    elif args[0] == "list":
      bets = get_all_objects("bet")
      bet_ids = []
      for bet in bets:
        if int(bet.winner) == 0:
          bet_ids.append(bet.code)
      if len(bet_ids) == 0:
        await ctx.send("No undecided bets.")
      for bet_id in bet_ids:
        embedd = await create_bet_embedded(bet_id)
        if embedd == None:
          await ctx.send("Identifier Not Found")
          return
        msg = await ctx.send(embed=embedd)
        bet = get_from_list("bet", bet_id)
        bet.message_ids.append((msg.id, msg.channel.id))
        replace_in_list("bet", bet.code, bet)

    elif len(arg) == 8:
      embedd = await create_bet_embedded(arg)
      if embedd == None:
        await ctx.send("Identifier Not Found")
        return
      msg = await ctx.send(embed=embedd)
      bet = get_from_list("bet", arg)
      bet.message_ids.append((msg.id, msg.channel.id))
      replace_in_list("bet", bet.code, bet)
      await ctx.message.delete()
    else:
      await ctx.send("Not valid command. Use $bet help to get list of commands")

  elif len(args) == 2:
    if args[0] == "cancel" and len(args[1]) == 8:
      bet = get_from_list("bet", args[1])
      if bet == None:
        await ctx.send("Identifier Not Found")
        return
      match = get_from_list("match", bet.match_id)
      if match.date_closed == None:
        
        #match.bet_ids.remove(bet.code)
        #replace_in_list("match", match.code, match)
        embedd = await create_match_embedded(match.code)
        await edit_all_messages(match.message_ids, embedd)
        
        for msg_id in bet.message_ids:
          try:
            channel = await bot.fetch_channel(msg_id[1])
            msg = await channel.fetch_message(msg_id[0])
            
            await msg.delete()
          except Exception as e:
            print("no msg found")
          
        remove_from_active_ids(bet.user_id, bet.code)
        await ctx.send(remove_from_list("bet", args[1]))
        
      else:
        await ctx.send("Match betting has closed cannot ")
    else:
      await ctx.send("Not valid command. Use $bet help to get list of commands")
    
  elif len(args) == 3:
    match_id, team_num, amount = args
    #$bet [match id] [team_num] [amount]
    if not amount.isdigit():
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
    if(user == None):
      user = create_user(ctx.author.id)

    balance_left = user.balance[-1][1] - int(amount)
    for bet_id in user.active_bet_ids:
      temp_bet = get_from_list("bet", bet_id)
      balance_left -= temp_bet.bet_amount
    if balance_left < 0:
      await ctx.send("You have bet " + str((-balance_left)) + " more that you have")
      return

    
    bet = Bet(code, match_id, ctx.author.id, int(amount), int(team_num), datetime.now())
    
    
    match.bet_ids.append(bet.code)
    replace_in_list("match", match.code, match)
    embedd = await create_match_embedded(match.code)
    await edit_all_messages(match.message_ids, embedd)
    add_to_list("bet", bet)
    add_to_active_ids(ctx.author.id, bet.code)
    embedd = await create_bet_embedded(bet.code)
    msg = await bot.get_channel(db["bet_channel_id"]).send(embed=embedd)
    
    await edit_all_messages(bet.message_ids, embedd)
    bet.message_ids.append((msg.id, msg.channel.id))
    replace_in_list("bet", bet.code, bet)
    if ctx.channel.id == db["bet_channel_id"]:
      await ctx.message.delete()
    
  
  else:
    await ctx.send("Not valid command. Use $bet help to get list of commands")


#debug
@bot.command()
async def debug(ctx, *args):
  if len(args) == 1:
    if args[0] == "help":
      await ctx.send(
      """$debug list [match, user, bet]: gives all info on all of object
$debug keys: gives all keys
$debug key "[key]": prints key as is (quotes only needed if there is a space)
$debug reassign "[original key]" "[new key]": replaces the original key with the new key (quotes only needed if there is a space)
$debug delete key "[key]": deletes key for database (quotes only needed if there is a space)
IF YOU ARE NOT PIG DONT MESS WITH DEBUG, WHAT YOU NEED IS SOMEWHERE ELSE""")

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
    if args[0] == "reassign":
      db[args[2]] = db[args[1]]
      del db[args[1]]
      await ctx.send("key " + args[1] + " is now " + args[2])
    

    elif args[0] == "delete" and args[1] == "key":
      del db[args[2]]
      await ctx.send("deleted " + str(args[2]))
    
    else:
      await ctx.send("Not valid command. Use $debug help to get list of commands")
  else:
    await ctx.send("Not valid command. Use $debug help to get list of commands")


@bot.command()
async def back(ctx):
  if not db["stage"]  == 0:
    db["stage"] = db["stage"] - 1
    print(db["stage"])
    #to do
    await ctx.send("Backed up for you :)")
  else:
    await ctx.send("Backed all the way up")


#assign bot spicific action to channel
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
$assign bets: where the end bets show up""")
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



#returns your own or someone else's balance
@bot.command()
async def balance(ctx, *args):
  if len(args) == 0:
    if(get_from_list("user", ctx.author.id) == None):
      create_user(ctx.author.id)
    print(ctx.author.id)
    embedd = await create_user_embedded(int(ctx.author.id))
    if embedd == None:
      await ctx.send("Identifier Not Found")
      return
    await ctx.send(embed=embedd)
    
  elif len(args) == 1:
    uid = args[0].replace("<","")
    uid = uid.replace(">","")
    uid = uid.replace("@","")
    uid = uid.replace("!","")
    if args[0] == "help":
      await ctx.send(
      """$balance gives your own balance
$balance [user's @]: gives balance of that user""")
    elif uid.isdigit():
      embedd = await create_user_embedded(int(uid))
      if embedd == None:
        await ctx.send("Identifier Not Found")
        return
      await ctx.send(embed=embedd)
    
  


#help
bot.remove_command('help')
@bot.command()
async def help(ctx):
  await ctx.send(
  """All commands have their own help. To go to help type $[command] help
$match: startes match setup and lists match
$back: goes backwards in match stage
$cancel: stop match setup
$bet: creates and lists bet
$assign: assigns what channels do what functions
$balance: returns your own or someone else's balance
$leaderboard: gives leaderboard of balances""")

#cancel
@bot.command()
async def cancel(ctx, *arg):
  if arg[0] == "help":
    await ctx.send("""$cancel: stops match setup""")

  else:
    await cancel_match()
    await ctx.send("Cancelled")

@bot.command()
async def leaderboard(ctx, *arg):
  if arg[0] == "help":
    await ctx.send("""$leaderboard: shows a learderboard""")

  else:
    embedd = await create_leaderboard_embedded()
    await ctx.send(embed=embedd)


#season reset command
@bot.command()
async def reset_season(ctx):
  return
  users = get_all_objects("user")
  for user in users:
    user.balance.pop()
    user.balance.append(("reset 1", 500, datetime.now()))
    replace_in_list("user", user.code, user)



#debug command
@bot.command()
async def reset_bet_winners_to_match_winners(ctx):
  return
  bets = get_all_objects("bet")
  for bet in bets:
    if not int(get_from_list("match", bet.match_id).winner) == 0:
      bet.winner = int(get_from_list("match", bet.match_id).winner)
      replace_in_list("bet", bet.code, bet)
      await ctx.send(embed=await create_bet_embedded(bet.code))


#debug command
@bot.command()
async def round_all_user_balances(ctx):
  return
  users = get_all_objects("user")
  for user in users:
    for bal in user.balance:
      
      user.balance[user.balance.index(bal)] = (user.balance[user.balance.index(bal)][0], round(user.balance[user.balance.index(bal)][1], 5), user.balance[user.balance.index(bal)][2])
    
    replace_in_list("user", user.code, user)


#debug command
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
    
#debug command
@bot.command()
async def add_var(ctx):
  return
  users = get_all_objects("user")
  for user in users:
    user.active_bet_ids = []
    replace_in_list("user", user.code, user)
    
    
  


keep_alive()
bot.run(os.getenv("TOKEN"))

