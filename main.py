#migrate user creator to user ID connected to a dictionary 
#add moddifacation when no on incorrect match creation
#jdshdfhfgh
#oihtfrg


import discord
import os
import random
from replit import db
from Match import Match
import jsonpickle
import math
from datetime import datetime

intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)

#matches are match_[identifyer]
#user balance isuser_[ID]
#logs are log_[ID] holds (log, date)



def get_all_matches(message):
  match_keys = db.prefix("match_")
  matchs = []
  for k in match_keys:
    #print(k)
    #print(db[k])
    matchs.append(jsonpickle.decode(db[k]))
  return matchs

def is_key(key):
  keys = db.keys()
  return key in keys

def get_uniqe_code(prefix:str):
  full_keys = db.prefix(prefix + "_")
  codes = full_keys[len(prefix) + 1:]
  print(codes)
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

async def delete_all_messages():
  for id in db["message_ids"]:
    bot_message = await bot.get_channel(db["creation_channel_id"]).fetch_message(id)
    await bot_message.delete()
  db["message_ids"] = []


async def cancel_match():
  if (db["delete_messages"]):
    await delete_all_messages()
  
  db["stage"] = 0
  if "current_user" in db.keys():
    del db["current_user"]
  if "current_t1_name" in db.keys():
    del db["current_t1_name"]
  if "current_t2_name" in db.keys():
    del db["current_t2_name"]
  if "current_old_t1_odds" in db.keys():
    del db["current_old_t1_odds"]
  if "current_old_t2_odds" in db.keys():
    del db["current_old_t2_odds"]
  if "current_t1_odds" in db.keys():
    del db["current_t1_odds"]
  if "current_t2_odds" in db.keys():
    del db["current_t2_odds"]
  if "tournament_name" in db.keys():
    del db["tournament_name"]

def roundup(x):
    return int(math.ceil(x * 1000)) / 1000

@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))
    db["stage"] = 0


@bot.event
async def on_message(message):
  
  if message.author == bot.user:
    return
  print(message.author)
  print(message.content)
  print("\n")

  #hard reset but logs
  if message.content == "$clear the database please and thank you":
    all_keys = db.keys()
    keys = []
    for k in all_keys:
      if not k.startswith("log"):
        keys.append(k)
    
    db["log_" + get_uniqe_code("log")] = jsonpickle.encode(("a little called " + message.author.name + " ID: " + str(message.author.id) + " cleared database \nkeys include " + str(keys)), datetime.now())

    for k in keys:
      del db[k]
    await message.channel.send("Good Bye World")

    return

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
  #hard reset + logs
  if message.content == "$clear the database please and thank youwfbjhwvfhdsufgiewgvuwegwgyufvehwwfevfuw":
    keys = db.keys()
    db["log_" + get_uniqe_code("log")] = jsonpickle.encode(("a little called " + message.author.name + " ID: " + str(message.author.id) + " cleared database AND LOGS\nkeys include " + str(keys)), datetime.now())
    for k in keys:
      del db[k]
    
    await message.channel.send("Good Bye World")
    return

  #match hard reset
  if message.content == "$clear the match database please and thank you":
    keys = db.prefix("match_")
    db["log_" + get_uniqe_code("log")] = jsonpickle.encode(("a little called " + message.author.name + " ID: " + str(message.author.id) + " cleared matches\nkeys include " + str(keys)), datetime.now())
    for k in keys:
      del db[k]
    await message.channel.send("Good Bye Matches")
    return



  message_text_lower = message.content.lower()



  #help
  if message_text_lower.startswith("$help"):
    await message.channel.send(
      """$match: startes match setup
$back: goes backwards in match stage
$cancel: stop match setup or a bet
$bet [match id] [team] [ammount]: you make a bet on the match with match id on the team ("1" for first team listed "2" for second team listed) ammount is whole numbers only
$assign: assigns what channels do what functions""")


  #cancel
  elif message_text_lower == "$cancel":
    cancel_argument = message_text_lower[8:]
    
    if cancel_argument == "help":
      await message.channel.send("""match: stops match setup
bet [id]: cancels bet with that id""")

    elif cancel_argument == "match":
      await cancel_match()
      await message.channel.send("Cancelled")

    elif cancel_argument.startswith("bet"):
      bet_id = cancel_argument[4:]
      #jdshdfhfgh

    else:
      await message.channel.send("Not valid command. Use $cancel help to get list of commands")

  #assign bot spicific action to channel
  elif message_text_lower.startswith("$bet"):
    
    assign_argument = message_text_lower[5:]
    key = "match_" + assign_argument[:8]
    
    db[]
    
    
    #oihtfrg


  #assign bot spicific action to channel
  elif message_text_lower.startswith("$assign"):
    assign_argument = message_text_lower[8:]
    if assign_argument == "help":
      await message.channel.send(
      """match creation: where match creation takes place
match list: were the end matches show up
predictions: where you make the predictions and check balance""")
    elif assign_argument == "match creation":
      db["creation_channel_id"] = message.channel.id
      await message.channel.send("This channel is now the match creation channel")
    elif assign_argument == "match list":
      db["list_channel_id"] = message.channel.id
      await message.channel.send("This channel is now the match list channel")
    elif assign_argument == "predictions":
      db["predictions_channel_id"] = message.channel.id
      await message.channel.send("This channel is now the prediction channel")
    else:
      await message.channel.send("Not a valid command do $assign help for list of commands")


  #settings
  elif message_text_lower.startswith("$setting"):
    setting_argument = message_text_lower[9:]
    if setting_argument.startswith("delete messages"):
      setting_condition = setting_argument[16:]
      if setting_condition == "yes" or setting_condition == "true":
        db["delete_messages"] = True
        await message.delete()
      elif setting_condition == "no" or setting_condition == "false":
        db["delete_messages"] = False
        await message.channel.send("Delete messages disabled")
      else:
        await message.channel.send("Invalid condition please enter yes or no")


  #debug
  elif message_text_lower.startswith("$debug"):
    debug_argument = message_text_lower[7:]
    if debug_argument == "help":
      await message.channel.send(
        """match: gives all info on all matches
match [argument]: gives all values of match argument
match help: lists the matches arguments""")

    elif debug_argument.startswith("match"):
      match_argument = debug_argument[6:]
      show_code = match_argument.endswith("code")

      if match_argument == "help":
        await message.channel.send(
      """team 1/team 1 names: team 1 name 
team 2/team 1 names: team 2 name
team 1 odds: team 1 odds
team 2 odds: team 2 odds
team 1 old odds: team 1 old odds
team 2 old odds: team 2 old odds
teams: [team 1] vs [team 2]
team odds: [team 1] vs [team 2] / [team 1 odds] vs [team 2 odds]
tournament names: all tournament names
odds sources: all odds sources
creator: all creators
codes: all match identifiers
all: lists all peramaters

add "code" to the end to add the match code to the end""")
      elif match_argument.startswith("team 1") or match_argument.startswith("team 1 names"):
        matches = get_all_matches()
        output = ""
        team1s = [t for t in matches.t1]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(team1s)):
            output += team1s[x] + " " + codes[x] + ", "
        else:
          for x in range(len(team1s)):
            output += team1s[x] + ", "

        output = output[:-2]
        await message.channel.send(output)

      elif match_argument.startswith("team 2") or match_argument.startswith("team 2 names"):
        matches = get_all_matches()
        output = ""
        team2s = [t for t in matches.t2]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(team2s)):
            output += team2s[x] + " " + codes[x] + ", "
        else:
          for x in range(len(team2s)):
            output += team2s[x] + ", "

        output = output[:-2]
        await message.channel.send(output)

      elif match_argument.startswith("team 1 odds"):
        matches = get_all_matches()
        output = ""
        team1_odds = [t for t in matches.t1o]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(team1_odds)):
            output += str(team1_odds[x]) + " " + codes[x] + ", "
        else:
          for x in range(len(team1_odds)):
            output += str(team1_odds[x]) + ", "

        output = output[:-2]
        await message.channel.send(output)

      elif match_argument.startswith("team 2 odds"):
        matches = get_all_matches()
        output = ""
        team2_odds = [t for t in matches.t2o]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(team2_odds)):
            output += str(team2_odds[x]) + " " + codes[x] + ", "
        else:
          for x in range(len(team2_odds)):
            output += str(team2_odds[x]) + ", "

        output = output[:-2]
        await message.channel.send(output)

      elif match_argument.startswith("team 1 old odds"):
        matches = get_all_matches()
        output = ""
        team1_odds = [t for t in matches.t1oo]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(team1_odds)):
            output += str(team1_odds[x]) + " " + codes[x] + ", "
        else:
          for x in range(len(team1_odds)):
            output += str(team1_odds[x]) + ", "

        output = output[:-2]
        await message.channel.send(output)

      elif match_argument.startswith("team 2 old odds"):
        matches = get_all_matches()
        output = ""
        team2_odds = [t for t in matches.t2oo]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(team2_odds)):
            output += str(team2_odds[x]) + " " + codes[x] + ", "
        else:
          for x in range(len(team2_odds)):
            output += str(team2_odds[x]) + ", "

        output = output[:-2]
        await message.channel.send(output)
      
      elif match_argument.startswith("teams"):
        matches = get_all_matches()
        output = ""
        team1s = [t for t in matches.t1]
        team2s = [t for t in matches.t2]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(team1s)):
            output += team1s[x] + " vs " + team2s[x] + " " + codes[x] + ", "
        else:
          for x in range(len(team1s)):
            output += team1s[x] + " vs " + team2s[x] + ", "

        output = output[:-2]
        await message.channel.send(output)

      
      elif match_argument.startswith("team odds"):
        matches = get_all_matches()
        output = ""
        team1s = [t for t in matches.t1]
        team2s = [t for t in matches.t2]
        team1_odds = [t for t in matches.t1o]
        team2_odds = [t for t in matches.t2o]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(team1s)):
            output += team1s[x] + " vs " + team2s[x] + " " + str(team1_odds[x]) + " / " + str(team2_odds[x]) + " " + codes[x] + ", "
        else:
          for x in range(len(team1s)):
            output += team1s[x] + " vs " + team2s[x] + " " + str(team1_odds[x]) + " / " + str(team2_odds[x]) + ", "

        output = output[:-2]
        await message.channel.send(output)

      elif match_argument.startswith("team old odds"):
        matches = get_all_matches()
        output = ""
        team1s = [t for t in matches.t1]
        team2s = [t for t in matches.t2]
        team1_odds = [t for t in matches.t1o]
        team2_odds = [t for t in matches.t2o]
        team1_old_odds = [t for t in matches.t1oo]
        team2_old_odds = [t for t in matches.t2oo]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(team1s)):
            output += team1s[x] + " vs " + team2s[x] + ", odds: " + str(team1_odds[x]) + " / " + str(team2_odds[x]) + ", old odds: " + str(team1_old_odds[x]) + " / " + str(team2_old_odds[x]) + " " + codes[x] + ", "
        else:
          for x in range(len(team1s)):
            output += team1s[x] + " vs " + team2s[x] + " " + str(team1_odds[x]) + " / " + str(team2_odds[x]) + ", "

        output = output[:-2]
        await message.channel.send(output)

      elif match_argument.startswith("tournament names"):
        matches = get_all_matches()
        output = ""
        tournament_names = [t for t in matches.tournament_name]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(tournament_names)):
            output += tournament_names[x] + " " + codes[x] + ", "
        else:
          for x in range(len(tournament_names)):
            output += tournament_names[x] + ", "

        output = output[:-2]
        await message.channel.send(output)

      elif match_argument.startswith("odds sources"):
        matches = get_all_matches()
        output = ""
        odds_sources = [t for t in matches.odds_source]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(odds_sources)):
            output += odds_sources[x] + " " + codes[x] + ", "
        else:
          for x in range(len(odds_sources)):
            output += odds_sources[x] + ", "

        output = output[:-2]
        await message.channel.send(output)

      elif match_argument.startswith("creators"):
        matches = get_all_matches()
        output = ""
        creators = [t for t in matches.creator]
        if show_code:
          codes = [c for c in matches.codes]
          for x in range(len(creators)):
            output += str(creators[x]) + " " + codes[x] + ", "
        else:
          for x in range(len(creators)):
            output += str(creators[x]) + ", "

        output = output[:-2]
        await message.channel.send(output)
      
      elif match_argument.startswith("codes"):
        matches = get_all_matches()
        output = ""
        codes = [c for c in matches.codes]
        for x in range(len(codes)):
          output += codes[x] + ", "

        output = output[:-2]
        await message.channel.send(output)
      
      elif debug_argument == "match":
        matches = get_all_matches()
        output = ""
        team1s = [m.t1 for m in matches]
        team2s = [m.t2 for m in matches]
        team1_odds = [m.t1o for m in matches]
        team2_odds = [m.t2o for m in matches]
        team1_old_odds = [m.t1oo for m in matches]
        team2_old_odds = [m.t2oo for m in matches]
        tournament_names = [m.tournament_name for m in matches]
        odds_sources = [m.odds_source for m in matches]
        creators = [m.creator for m in matches]
        date_created = [m.date_created for m in matches]
        codes = [m.identifyer for m in matches]

        for x in range(len(team1s)):
          date_formatted = date_created[x].strftime("%d/%m/%Y %H:%M:%S")
          output += "Teams: " + team1s[x] + " vs " + team2s[x] + ", Odds: " + str(team1_odds[x]) + " / " + str(team2_odds[x]) + ", Old Odds: " + str(team1_old_odds[x]) + " / " + str(team2_old_odds[x]) + ", Tournament Name: " + tournament_names[x] + ", Odds Source: " + odds_sources[x] + ", Creator: " + str(bot.get_user(creators[x])) + "\nCreated On: " + date_formatted + ", Identiifyer Code: " + codes[x] + "\n"
        if output == "":
          return;
        output = output[:-1]
        await message.channel.send(output)
      else:
        await message.channel.send("invalid command\nuse $debug match help for list of commands")

    elif debug_argument == "keys":
      await message.channel.send(str(db.keys())[1:-1])
      
    elif debug_argument.startswith("reassign"):
      reassign_argument = debug_argument[8:]
      original,new = reassign_argument.split('/', 1)
      db[new] = db[original]
      del db[original]
      await message.channel.send("key " + original + " is now " + new)
      
    else:
      await message.channel.send("invalid command\nuse $debug help for list of commands")


  
  
  
  else:
    #match creator
    if not "stage" in db.keys():
      db["stage"] = 0

    stage = db["stage"]

    if message_text_lower == "$back":
      message_ids = db["message_ids"]
      message_ids.append(message.id)

      db["stage"] = db["stage"] - 1
      print(db["stage"])
      reply_message = await message.channel.send("Backed up for you :)")

      message_ids.append(reply_message.id)
      db["message_ids"] = message_ids

      return
    
    if message_text_lower == "$match":
      if message.channel.id == db["creation_channel_id"]:
        await cancel_match()
        db["message_ids"] = []
        message_ids = db["message_ids"]
        message_ids.append(message.id)

        reply_message = await message.channel.send("What is Team 1's Name")
        message_ids.append(reply_message.id)
        db["message_ids"] = message_ids

        db["current_user"] = message.author.id
        db["stage"] = 1
        return
      else:
        channel = await bot.fetch_channel(db["creation_channel_id"])
        await message.channel.send("Please put command in" + str(channel.mention))

    if stage == 1:
      if message.author.id == db["current_user"]:
        message_ids = db["message_ids"]
        message_ids.append(message.id)
        db["message_ids"] = message_ids

        db["current_t1_name"] = message.content
        reply_message = await message.channel.send("What is Team 2's Name")
        
        reply_message_id = reply_message.id
        message_ids.append(reply_message_id)
        db["message_ids"] = message_ids

        db["stage"] = 2

    elif stage == 2:
      if message.author.id == db["current_user"]:
        message_ids = db["message_ids"]
        message_ids.append(message.id)

        db["message_ids"] = message_ids

        db["current_t2_name"] = message.content
        reply_message = await message.channel.send("What is Team 1's Odds\nEnter in the amount you would get if you bet 1")
      
        message_ids.append(reply_message.id)
        db["message_ids"] = message_ids

        db["stage"] = 3

    elif stage == 3:
      if message.author.id == db["current_user"]:
        message_ids = db["message_ids"]
        message_ids.append(message.id)

        db["message_ids"] = message_ids

        s = message.content
        stemp = s.replace('.','')
        if (stemp.isdigit() and (s.find('.') == -1 or s.find('.') == 1)):
          reply_message = await message.channel.send("What is Team 2's Odds\nEnter in the amount you would get if you bet 1")
      
          message_ids.append(reply_message.id)
          db["message_ids"] = message_ids

          db["current_old_t1_odds"] = float(s)
          db["stage"] = 4
        else:
          reply_message = await message.channel.send("Please enter a valid number")
      
          message_ids.append(reply_message.id)
          db["message_ids"] = message_ids



    elif stage == 4:
      if message.author.id == db["current_user"]:
        message_ids = db["message_ids"]
        message_ids.append(message.id)

        db["message_ids"] = message_ids

        s = message.content
        stemp = s.replace('.','')

        if (stemp.isdigit() and (s.find('.') == -1 or s.find('.') == 1)):
          reply_message = await message.channel.send("Do you want to balance the odds?")
      
          message_ids.append(reply_message.id)
          db["message_ids"] = message_ids

          db["current_old_t2_odds"] = float(s)
          db["stage"] = 5
        else:
          reply_message = await message.channel.send("Please enter a valid number")
      
          message_ids.append(reply_message.id)
          db["message_ids"] = message_ids


    elif stage == 5:
      if message.author.id == db["current_user"]:
        message_ids = db["message_ids"]
        message_ids.append(message.id)

        db["message_ids"] = message_ids
        
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
          print()
          reply_message = await message.channel.send("The new odds are " + str(db["current_t1_odds"]) + " / " + str(db["current_t2_odds"]) + "\nWhat is the Tournament Name")
    
          message_ids.append(reply_message.id)
          db["message_ids"] = message_ids

          db["stage"] = 6;
        elif message.content.lower() == "no":
          reply_message = await message.channel.send("What is the Tournament Name")
    
          message_ids.append(reply_message.id)
          db["message_ids"] = message_ids

          db["current_t1_odds"] = db["current_old_t1_odds"]
          db["current_t2_odds"] = db["current_old_t2_odds"]
          db["stage"] = 6
        else:
          reply_message = await message.channel.send("Please enter either yes or no")

          message_ids.append(reply_message.id)
          db["message_ids"] = message_ids



    elif stage == 6:
      if message.author.id == db["current_user"]:

        message_ids = db["message_ids"]
        message_ids.append(message.id)

        db["message_ids"] = message_ids
        
        db["tournament_name"] = message.content
        reply_message = await message.channel.send("Where are the odds from")
      
        message_ids.append(reply_message.id)
        db["message_ids"] = message_ids

        db["stage"] = 7
          
    elif stage == 7:
      if message.author.id == db["current_user"]:
        
        message_ids = db["message_ids"]
        message_ids.append(message.id)

        odds_source = message.content  

        code = get_uniqe_code("match")
        

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
        date_formatted = cmatch.date_created.strftime("%d/%m/%Y %H:%M:%S")
        s += "Teams: " + cmatch.t1 + " vs " + cmatch.t2 + "\nOdds: " + str(cmatch.t1o) + " / " + str(cmatch.t2o) + "\nOld Odds: " + str(cmatch.t1oo) + " / " + str(cmatch.t2oo) + "\nTournament Name: " + cmatch.tournament_name + "\nOdds Source: " + cmatch.odds_source + "\nCreator: " + bot.get_user(cmatch.creator).name + "\nCreated On: " + str(date_formatted) + "\nIdentifyer Code: " + cmatch.identifyer
      
        reply_message = await message.channel.send(s)
      
        message_ids.append(reply_message.id)
        db["message_ids"] = message_ids

        db["stage"] = 8  
    elif stage == 8:
      if message.author.id == db["current_user"]:
        
        message_ids = db["message_ids"]
        message_ids.append(message.id)

        if message.content.lower() == "yes":
          db["stage"] = 0
          cmatch = jsonpickle.decode(db["current_match"])
          db["match_" + cmatch.identifyer] = jsonpickle.encode(cmatch)
          await bot.get_channel(db["list_channel_id"]).send("Teams: " + cmatch.t1 + " vs " + cmatch.t2 + "\nOdds: " + str(cmatch.t1o) + " / " + str(cmatch.t2o) + "\nOld Odds: " + str(cmatch.t1oo) + " / " + str(cmatch.t2oo) + "\nTournament Name: " + cmatch.tournament_name + "\nOdds Source: " + cmatch.odds_source + "\nCreator: " + bot.get_user(cmatch.creator).name + "\nCreated On: " + cmatch.date_created + "\nIdentifyer Code: " + cmatch.identifyer)
          await cancel_match()
        elif message.content.lower() == "no":
          #to-do add moddifacation
          await message.channel.send("Cancelled")
          await cancel_match()

          db["stage"] = 0
        else:
          reply_message = await message.channel.send("Please enter either yes or no")
    
          message_ids.append(reply_message.id)
          db["message_ids"] = message_ids






bot.run(os.getenv("TOKEN"))
