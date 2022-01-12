import discord
import os
import random
from replit import db

client = discord.Client()

#matches are M[identifyer]
#user balance is UB[ewbfuefwvuewbuefw]
#


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))
    db["stage"] = 0


@client.event
async def on_message(message):
  if message.author == client.user:
    return
  print(message.author)
  #help
  if message.content.startswith("$help") | message.content.startswith("$Help"):
    await message.channel.send("$match startes match setup\n$cancel stops match setup")


  #match creator
  stage = db["stage"]
  user = db["current_user"]
  
  if stage == 0:
    if message.content.startswith("$match") | message.content.startswith("$Match"):
      await message.channel.send("What is Team 1's Name")
      db["current_user"] = message.author
      db["stage"] = 1

  elif stage == 1:
    if message.author == db["current_user"]:
      db["current_t1name"] = message.content
      await message.channel.send("What is Team 2's Name")
      db["stage"] = 2

  elif stage == 2:
    if message.author == db["current_user"]:
      db["current_t2name"] = message.content
      await message.channel.send("What is Team 1's Odds")
      db["stage"] = 3

  elif stage == 3:
    if message.author == db["current_user"]:
      s = message.content
      stemp = s.replace('.','')

      if (stemp.isdigit and (s.find('.') == 0 or s.find('.') == 1)):
        await message.channel.send("What is Team 2's Odds")
        db["current_t1odds"] = float(s)
        db["stage"] = 4
      else:
        await message.channel.send("Please enter a valid number")


  elif stage == 4:
    if message.author == db["current_user"]:
      s = message.content
      stemp = s.replace('.','')

      if (stemp.isdigit and (s.find('.') == 0 or s.find('.') == 1)):
        await message.channel.send("What is the Tournament Name")
        db["current_t2odds"] = float(s)
        db["stage"] = 5
      else:
        await message.channel.send("Please enter a valid number")

  elif stage == 5:
    if message.author == db["current_user"]:
      db["tournament_name"] = message.content
      await message.channel.send("Where are the odds from")
      db["stage"] = 6
        
  elif stage == 6:
    if message.author == db["current_user"]:
      odds_source = message.content
      await message.channel.send("Where are the odds from")
      db["stage"] = 0     

      match_keys = db.prefix("prefix")

      #create random hexadecimal number with a length of 8
      random.seed()
      code = str(hex(random.randint(0,2**32-1))[2:]).zfill(8)

      cMatch = Match(db["current_t1name"], db["current_t2name"], db["current_t1odds"], db["current_t2odds"], db["tournament_name"], odds_source, user, code)
      


  
  #cancel
  if message.content.startswith("$cancel") | message.content.startswith("$Cancel"):
    db["stage"] = 0
    await message.channel.send("Cancelled")
  
    
    

    
    
client.run(os.getenv("TOKEN"))