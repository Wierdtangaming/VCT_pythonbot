
# add moddifacation when no on incorrect match creation
# test bet list with and without await
# have it replace by code not by value
# test prefix unique with 1 long in test code

from io import BytesIO
import collections
#git clone https://github.com/Pycord-Development/pycord
#cd pycord
#python3 -m pip install -U .[voice]

#pip install git+https://github.com/Pycord-Development/pycord
#poetry add git+https://github.com/Pycord-Development/pycord
import discord
from discord.commands import Option, OptionChoice, SlashCommandGroup
from discord.ui import InputText, Modal
from discord.ext import tasks, commands
import os
import random
import jsonpickle
from Match import Match
from Bet import Bet
from User import User, get_multi_graph_image, all_user_unique_code, get_all_unique_balance_ids, num_of_bal_with_name
from dbinterface import  get_date, get_setting, get_channel_from_db, set_channel_in_db, get_all_db, get_from_db, add_to_db
from colorinterface import hex_to_tuple, get_color, add_color, remove_color, rename_color, recolor_color
import math
from decimal import *
from PIL import Image, ImageDraw, ImageFont
from convert import ambig_to_obj, get_user_from_at, get_user_from_id, get_user_from_member, user_from_autocomplete_tuple, get_user_from_username, usernames_to_users
from objembed import create_match_embedded, create_match_list_embedded, create_bet_list_embedded, create_bet_embedded, create_user_embedded, create_leaderboard_embedded, create_payout_list_embedded, create_award_label_list_embedded
from savefiles import  get_all_names, backup
import time
from savedata import backup_full, save_savedata_from_github, are_equivalent, zip_savedata
import matplotlib.colors as mcolors
import secrets

from sqlaobjs import Session

if not os.path.isfile("savedata.db"):
  print("savedata.db does not exist.\nquitting")
  quit()
  


intents = discord.Intents.all()

bot = commands.Bot(intents=intents, command_prefix="$")

gid = get_setting("guild_ids")


# matches are in match_list_[identifier] one key contains 50 matches, indentifyer incrimentaly counts up
# user is in user_list_[identifier] one key contains 50 users, indentifyer incrimentaly counts up
# bet is in bet_list_[identifier] one key contains 50 users, indentifyer incrimentaly counts up
# logs are log_[ID] holds (log, date)




def get_all_available_matches():
  matches = get_all_objects("match")
  match_list = []
  for match in matches:
    if int(match.winner) == 0:
      match_list.append(match)
  return match_list

def available_matches_name_code():
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

def all_matches_name_code():
  matches = get_all_objects("match")
  match_t_list = []
  for match in matches:
    if match.winner != 0:
      s = f"Concluded: {match.t1} vs {match.t2}, {match.tournament_name}"
      if len(s) >= 100:
        s = f"Con: {match.t1} vs {match.t2}, {match.tournament_name}"
        if len(s) >= 100:
          s = f"Con: {match.t1}/{match.t2}, {match.tournament_name}"
          if len(s) >= 100:
            tsplit = match.tournament_name.split(" ")[0]
            s = f"Con: {match.t1}/{match.t2}, {tsplit}"
            
      match_t_list.append((s, match))
    else:
      match_t_list.append((f"{match.t1} vs {match.t2}, {match.tournament_name}", match))
  return match_t_list

async def available_bets_name_code(bot):
  matches = get_all_objects("match")
  bet_list = []
  id_dict = {}
  for match in matches:
    if match.date_closed is None:
      for bet_id in match.bet_ids:
        bet = get_from_list("bet", bet_id)
        if bet.user_id in id_dict:
          name = id_dict[bet.user_id]
        else: 
          name = get_from_list("user", bet.user_id).username
          id_dict[bet.user_id] = name
        bet_list.append((f"{name}: {bet.amount_bet} on {bet.get_team()}", bet))
  return bet_list

async def current_bets_name_code(bot):
  bets = get_all_objects("bet")
  bet_list = []
  id_dict = {}
  for bet in bets:
    if bet.winner == 0:
      if bet.user_id in id_dict:
        name = id_dict[bet.user_id]
      else: 
        name = get_from_list("user", bet.user_id).username
        id_dict[bet.user_id] = name
      bet_list.append((f"{name}: {bet.amount_bet} on {bet.get_team()}", bet))
  return bet_list

async def all_bets_name_code(bot):
  bets = get_all_objects("bet")
  bet_list = []
  id_dict = {}
  for bet in bets:
    if bet.winner != 0:
      if bet.user_id in id_dict:
        name = id_dict[bet.user_id]
      else: 
        name = get_from_list("user", bet.user_id).username
        id_dict[bet.user_id] = name
        
      bet_list.append((f"Paid out: {name}: {bet.amount_bet} on {bet.get_team()}", bet))
    else:
      bet_list.append((f"{name}: {bet.amount_bet} on {bet.get_team()}", bet))
  return bet_list


def get_users_from_multiuser(compare, session=None):
  usernames_split = compare.split(" ")
  
  users = usernames_to_users(compare, session)

  
  if len(users) == 1:
    return "You need to compare more than one user."

  
  usernames = " ".join([user.username for user in users])

  for username_word in usernames_split:
    if username_word not in usernames:
      return f"User {username_word} not found."

  return users


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
  user = ambig_to_obj(user_ambig, "User")
  if user is None:
    return "User not found"
  indices = [i for i, x in enumerate(user.balances) if x[0] == balance_id]
  if len(indices) > 1:
    return "More than one balance_id found"
  elif len(indices) == 0:
    return "No balance_id found"
  else:
    balat = user.balances[indices[0]]
    user.balances[indices[0]] = (new_balance_id, balat[1], balat[2])
    replace_in_list("user", user.code, user)


def delete_balance_id(user_ambig, balance_id):
  print(balance_id)
  user = ambig_to_obj(user_ambig, "User")
  if user is None:
    return "User not found"
  indices = [i for i, x in enumerate(user.balances) if x[0] == balance_id]
  if len(indices) > 1:
    print("More than one balance_id found")
  elif len(indices) == 0:
    return "No balancesn id found"
  reset_range = user.get_to_reset_range(indices[0])
  
  index = indices[0]
  diff = user.balances[index][1] - user.balances[index-1][1]
  print(diff)
  for i in reset_range:
    bal_list = list(user.balances[i])
    bal_list[1] = bal_list[1] - diff
    user.balances[i] = tuple(bal_list)
  balat = user.balances[indices[0]]
  
  user.balances.remove(balat)
  replace_in_list("user", user.code, user)
  print(f"removed {balance_id}")
  return "Removed"


def print_all_balances(user_ambig):
  user = ambig_to_obj(user_ambig, "User")
  if user is None:
    return None

  [print(bal[0], bal[1]) for bal in user.balances]


async def edit_all_messages(ids, embedd):
  for id in ids:
    try:
      channel = await bot.fetch_channel(id[1])
      msg = await channel.fetch_message(id[0])
      title = msg.embeds[0].title
      embedd.title = title
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

def get_unique_code(prefix, session=None):
  if session is None:
    with Session.begin() as session:
      return get_unique_code(prefix, session)
  all_objs = get_all_db(prefix, session)
  codes = [str(k.code) for k in all_objs]
  code = ""
  copy = True
  while copy:
    copy = False

    random.seed()
    code = str(secrets.token_hex(4))
    for k in codes:
      if k == code:
        copy = True
  return code


def create_user(user_id, username):
  random.seed()
  color = secrets.token_hex(3)
  user = User(user_id, username, color, get_date())
  print(jsonpickle.encode(user))
  add_to_db("User", user)
  return user




def add_to_active_ids(user_ambig, bet_ambig, session=None):
  if session is None:
    with Session.begin() as session:
      add_to_active_ids(user_ambig, bet_ambig, session)
  if (user := ambig_to_obj(user_ambig, "User", session)) is None: return None
  if (bet := ambig_to_obj(bet_ambig, "Bet", session)) is None: return None

  user.active_bet_ids.append((bet.code, bet.match_id))


def remove_from_active_ids(user_ambig, bet_id, session=None):
  if session is None:
    with Session.begin() as session:
      remove_from_active_ids(user_ambig, bet_id, session)
  
  if (user := ambig_to_obj(user_ambig, "User", session)) is None: return None
  
  if (t := next((t for t in user.active_bet_ids if bet_id == t[0]), None)) is None:
    print("Bet_id Not Found")
    return
  user.active_bet_ids.remove(t)


def add_balance_user(user_ambig, change, description, date, session=None):
  if session is None:
    with Session.begin() as session:
      return add_balance_user(user_ambig, change, description, date, session=session)
      
  user = ambig_to_obj(user_ambig, "User")
  if user is None:
    return None
  user.balances.append((description, Decimal(str(round(user.balances[-1][1] + Decimal(str(change)), 5))), date))
  user.balances.sort(key=lambda x: x[2])
  return user

#returns user with new balances
def change_prev_balances(user, balance_id, new_amount):
  index = [x for x, y in enumerate(user.balances) if y[0] == str(balance_id)]
  if not len(index) == 1:
    print(str(len(index)) + " copy of id")
    return None
    
  index = index[0]

  difference = user.balances[index][1] - new_amount

  for i in range(index, len(user.balances)):
    if i+1 < len(user.balances):
      difference = user.balances[i+1][1] - user.balances[i][1]
    user.balances[i] = (user.balances[i][0], new_amount, user.balances[i][2])
    new_amount = user.balances[i][1] + difference
  return user


  


def roundup(x):
  return math.ceil(Decimal(x) * Decimal(1000)) / Decimal(1000)


@bot.event
async def on_ready():
  print("Logged in as {0.user}".format(bot))
  print(bot.guilds)
  
  save_savedata_from_github()
  zip_savedata()
  if (not are_equivalent("backup.zip", "gitbackup.zip")):
    print("savedata not is not synced with github")
    
    if get_setting("override_savedata"):
      print("overriding savedata")
    else:
      print("quitting")
      quit()
      
  auto_backup_timer.start()
  print("\n-----------Bot Starting-----------\n")


@tasks.loop(minutes=20)
async def auto_backup_timer():
  from test import f
  if f:
    quit()
  f = True
  print("timer")
  backup_full()
  
  
#autocomplete start

#color picker autocomplete start
async def color_picker_autocomplete(ctx: discord.AutocompleteContext):  
  return [x.capitalize() for x in get_all_colors().keys() if ctx.value.lower() in x.lower()]
#color picker autocomplete end

#multi user autocomplete start
async def multi_user_list_autocomplete(ctx: discord.AutocompleteContext):
  value = ctx.value.strip()
  users = get_all_db("User")
  usernames_t = [(user.username, user.username.replace(" ", "-_-")) for user in users if user.hidden]
  clean_usernames = [username_t[0] for username_t in usernames_t]
  no_break_usernames = [username_t[1] for username_t in usernames_t]
  for username_t in usernames_t:
    value = value.replace(username_t[0], username_t[1])
  combined_values = value
  values = value.split(" ")
  if len(values) == 0:
    return clean_usernames
  last_value = values[-1]
  all_but = " ".join(values[:-1]).replace("-_-", " ")
  all = " ".join(values).replace("-_-", " ")
  if last_value not in no_break_usernames:
    auto_completes = []
    for username_t in usernames_t:
      if username_t[1] in combined_values:
        continue
      if username_t[1].startswith(last_value):
        auto_completes.append(f"{all_but} {username_t[0]}")
    return auto_completes
  auto_completes = [f"{all} {username_t[0]}" for username_t in usernames_t if username_t[1] not in combined_values]
  return auto_completes
#multi user autocomplete end

#autocomplete end


  

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




#assign start
assign = SlashCommandGroup(
  name = "assign", 
  description = "Assigns the discord channel it is put in to that channel type.",
  guild_ids = gid,
)

#assign matches start
@assign.command(name = "matches", description = "Where the end matches show up.")
async def assign_matches(ctx):
  set_channel_in_db("match", ctx.channel.id)
  
  await ctx.respond(f"<#{ctx.channel.id}> is now the match list channel.")
#assign matches end

#assign bets start
@assign.command(name = "bets", description = "Where the end bets show up.")
async def assign_bets(ctx):
  set_channel_in_db("bet", ctx.channel.id)
  await ctx.respond(f"<#{ctx.channel.id}> is now the bet list channel.")
#assign bets end

bot.add_application_command(assign)
#assign end


#award start
award = SlashCommandGroup(
  name = "award", 
  description = "Awards the money to someone's account. DON'T USE WITHOUT PERMISSION!",
  guild_ids = gid,
)

#user award autocomplete start
async def user_awards_autocomplete(ctx: discord.AutocompleteContext):
  member = ctx.options["user"]
  
  if member is None:
    return []
  
  user = get_user_from_id(member)
  
  award_labels = user.get_award_strings()
  
  auto_completes = [award_label for award_label in award_labels if ctx.value.lower() in award_label.lower()]
  
  return auto_completes
#user award autocomplete end  



#award give start
@award.command(name = "give", description = """Awards the money to someone's account. DON'T USE WITHOUT PERMISSION!""")
async def award_give(ctx, 
  amount: Option(int, "Amount you want to give or take."), description: Option(str, "Unique description of why the award is given."),
  user: Option(discord.Member, "User you wannt to award. (Can't use with users).", default = None, required = False),  
  users: Option(str, "Users you want to award. (Can't use with user).", autocomplete=multi_user_list_autocomplete, default = None, required = False)):
  
  if (user is not None) and (users is not None):
    await ctx.respond("You can't use compare and user at the same time.", ephemeral = True)
    return
  if (user is None) and (users is None):
    await ctx.respond("You must have either compare or user.", ephemeral = True)
    return
  
  with Session.begin() as session:
    if users is not None:
      users = get_users_from_multiuser(users, session)
      if isinstance(users, str):
        await ctx.respond(users, ephemeral = True)
        return
      code = all_user_unique_code("award", users)
      bet_id = f"award_{code}_{description}"
      
      print(bet_id)
      
      first = True
      for user in users:
        abu = add_balance_user(user, amount, bet_id, get_date(), session)
        embedd = await create_user_embedded(abu)
        if first:
          await ctx.respond(embed=embedd)
          first = False
        else:
          await ctx.interaction.followup.send(embed=embedd)
      return
    
    if (user := await get_user_from_member(ctx, user, session)) is None: return
    bet_id = "award_" + user.get_unique_code("award_") + "_" + description
    print(bet_id)
    abu = add_balance_user(user, amount, bet_id, get_date(), session)
    if abu is None:
      await ctx.respond("User not found.", ephemeral = True)
    else:
      embedd = await create_user_embedded(user, session)
      await ctx.respond(embed=embedd)
#award give end

#award list start
@award.command(name = "list", description = "Lists all the awards given to a user.")
async def award_list(ctx, user: Option(discord.Member, "User you want to list awards for.")):
  if (user := await get_user_from_member(ctx, user)) is None: return
  
  award_labels = user.get_award_strings()
  
  embedd = create_award_label_list_embedded(user, award_labels)
  await ctx.respond(embed=embedd)
  

#award rename start
@award.command(name = "rename", description = """Renames an award.""")
async def award_rename(ctx, user: Option(discord.Member, "User you wannt to award"), description: Option(str, "Unique description of why the award is given."), award: Option(str, "Description of award you want to rename.", autocomplete=user_awards_autocomplete)):
  
  with Session.begin() as session:
    if (user := await get_user_from_member(ctx, user, session)) is None: return
    
    award_labels = user.get_award_strings()
    
    if len(award) == 8:
      if award_label.endswith(award):
        award = award_label
    else:
      for award_label in award_labels:
        if award_label == award:
          award = award_label
          break
      else:
        await ctx.respond("Award not found.", ephemeral = True)
        return
      
    users = get_all_db("User")
    
    num = num_of_bal_with_name(award, users)
    
    if num > 1:
      await ctx.respond("There are multiple awards with this name.", ephemeral = True)
      return
    
    if user.change_award_name(award, description, session) is None:
      print(f"change_award_name not found. {award}\n{num}\n{user.code}.")
      await ctx.respond(f"Award not working {description}, {award}\n{num}\n{user.code}.", ephemeral = True)
    
    print(award)
    award_t = award.split(", ")[:-2]
    award = ", ".join(award_t)
    
    
    await ctx.respond(f"Award {award} renamed to {description}.")
#award rename end  



bot.add_application_command(award)
#award end

  

#balance start
@bot.slash_command(name = "balance", description = "Shows the last x amount of balance changes (awards, bets, etc).", aliases=["bal"], guild_ids = gid)
async def balance(ctx, user: Option(discord.Member, "User you want to get balance of.", default = None, required = False)):
  if user is None:
    user = get_from_db("User", ctx.author.id)
    print(user)
    if user is None:
      print("creating_user")
      user = create_user(ctx.author.id, ctx.author.display_name)
  else:
    if (user := await get_user_from_member(ctx, user)) is None: return
    
  embedd = await create_user_embedded(user)
  if embedd is None:
    await ctx.respond("User not found.")
    return
  await ctx.respond(embed=embedd)
#balance end



#bet start
betscg = SlashCommandGroup(
  name = "bet", 
  description = "Create, edit, and view bets.",
  guild_ids = gid,
)


#bet create modal start
class BetCreateModal(Modal):
  
  def __init__(self, match: Match, user: User, error=[None, None], session=None, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.match = match
    self.user = user
    
    if error[0] is None: 
      team_label = f"{match.t1} vs {match.t2}. Odds: {match.t1o} / {match.t2o}"
      if len(team_label) >= 45:
        team_label = f"{match.t1} vs {match.t2}, {match.t1o} / {match.t2o}"
        if len(team_label) >= 45:
          team_label = f"{match.t1} vs {match.t2}, {match.t1o}/{match.t2o}"
          if len(team_label) >= 45:
            team_label = f"{match.t1}/{match.t2}, {match.t1o}/{match.t2o}"
            if len(team_label) >= 45:
              firstt1w = match.t1.split(" ")[0]
              firstt2w = match.t2.split(" ")[0]
              team_label = f"{firstt1w} vs {firstt2w}. Odds: {match.t1o} / {match.t2o}"
              if len(team_label) >= 45:
                team_label = f"{firstt1w} vs {firstt2w}, {match.t1o} / {match.t2o}"
                if len(team_label) >= 45:
                  team_label = f"{firstt1w} vs {firstt2w}, {match.t1o}/{match.t2o}"
                  if len(team_label) >= 45:
                    team_label = f"{firstt1w}/{firstt2w}, {match.t1o}/{match.t2o}"
                    if len(team_label) >= 45:
                      team_label = f"{firstt1w[:15]}/{firstt2w[:15]}, {match.t1o}/{match.t2o}"
    else:
      team_label = error[0]
      
    self.add_item(InputText(label=team_label, placeholder=f'"1" for {match.t1} and "2" for {match.t2}', min_length=1, max_length=100))

    if error[1] is None: 
      amount_label = "Amount you want to bet."
    else:
      amount_label = error[1]
    self.add_item(InputText(label=amount_label, placeholder=f"Your available balance is {math.floor(user.get_balance(session))}", min_length=1, max_length=20))


  async def callback(self, interaction: discord.Interaction):
    with Session.begin() as session:
      match = self.match
      user = self.user
      team_num = self.children[0].value
      amount = self.children[1].value
      error = [None, None]
      
      if not is_digit(amount):
        print("Amount has to be a positive whole integer.")
        error[1] = "Amount must be a positive whole number."
      else:
        if int(amount) <= 0:
          print("Cant bet negatives.")
          error[1] = "Amount must be a positive whole number."
      
      if not (team_num == "1" or team_num == "2" or team_num.lower() == match.t1.lower() or team_num.lower() == match.t2.lower()):
        print("Team num has to either be 1 or 2.")
        error[0] = f'Team number has to be "1", "2", "{match.t1}", or "{match.t2}".'
      else:
        if team_num.lower() == match.t1.lower():
          team_num = "1"
        elif team_num.lower() == match.t2.lower():
          team_num = "2"

      if not match.date_closed is None:
        await interaction.response.send_message("Betting has closed you cannot make a bet.")

      code = get_unique_code("Bet", session)
      if error[1] is None:
        balance_left = user.get_balance(session) - int(amount)
        if balance_left < 0:
          print("You have bet " + str(math.ceil(-balance_left)) + " more than you have.")
          error[1] = "You have bet " + str(math.ceil(-balance_left)) + " more than you have."
      
      if not error == [None, None]:
        errortext = ""
        if error[0] is not None:
          errortext += error[0]
          if error[1] is not None:
            errortext += "\n"
        if error[1] is not None:
          errortext += error[1]
        await interaction.response.send_message(errortext, ephemeral = True)
        return

      color = code[:6]
      
      bet = Bet(code, match.t1, match.t2, match.tournament_name, int(amount), int(team_num), color, match.code, user.code, get_date())

      add_to_active_ids(user.code, bet, session)

      embedd = await create_bet_embedded(bet, f"New Bet: {user.username}, {amount} on {bet.get_team()}.")
      
      if (channel := await bot.fetch_channel(get_channel_from_db("bet", session))) == interaction.channel:
        inter = await interaction.response.send_message(embed=embedd)
        msg = await inter.original_message()
      else:
        await interaction.response.send_message(f"Bet created in {channel.mention}.", ephemeral = True)
        msg = await channel.send(embed=embedd)

      bet.message_ids.append((msg.id, msg.channel.id))
      add_to_db(bet, session)
      embedd = await create_match_embedded(match, "Placeholder", session)
      await edit_all_messages(match.message_ids, embedd)
#bet create modal end

#bet edit modal start
class BetEditModal(Modal):
  
  def __init__(self, match: Match, user: User, bet: Bet, session=None, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.match = match
    self.user = user
    self.bet = bet
    
    team_label = f"{match.t1} vs {match.t2}. Odds: {match.t1o} / {match.t2o}"
    if len(team_label) >= 45:
      team_label = f"{match.t1} vs {match.t2}, {match.t1o} / {match.t2o}"
      if len(team_label) >= 45:
        team_label = f"{match.t1} vs {match.t2}, {match.t1o}/{match.t2o}"
        if len(team_label) >= 45:
          team_label = f"{match.t1}/{match.t2}, {match.t1o}/{match.t2o}"
          if len(team_label) >= 45:
            firstt1w = match.t1.split(" ")[0]
            firstt2w = match.t2.split(" ")[0]
            team_label = f"{firstt1w} vs {firstt2w}. Odds: {match.t1o} / {match.t2o}"
            if len(team_label) >= 45:
              team_label = f"{firstt1w} vs {firstt2w}, {match.t1o} / {match.t2o}"
              if len(team_label) >= 45:
                team_label = f"{firstt1w} vs {firstt2w}, {match.t1o}/{match.t2o}"
                if len(team_label) >= 45:
                  team_label = f"{firstt1w}/{firstt2w}, {match.t1o}/{match.t2o}"
                  if len(team_label) >= 45:
                    team_label = f"{firstt1w[:15]}/{firstt2w[:15]}, {match.t1o}/{match.t2o}"
    
      
    self.add_item(InputText(label=team_label, placeholder=bet.get_team(), min_length=1, max_length=100, required=False))

    amount_label = f"Amount to bet. Balance: {math.floor(user.get_balance(session) + bet.amount_bet)}"
    self.add_item(InputText(label=amount_label, placeholder = bet.amount_bet, min_length=1, max_length=20, required=False))

  async def callback(self, interaction: discord.Interaction):
    with Session.begin() as session:
      match = self.match
      user = self.user
      bet = self.bet

      team_num = self.children[0].value
      if team_num == "":
        team_num = str(bet.team_num)
      amount = self.children[1].value
      if amount == "":
        amount = str(bet.amount_bet)
      error = [None, None]
      
      if not is_digit(amount):
        print("Amount has to be a positive whole integer.")
        error[1] = "Amount must be a positive whole number."
      else:
        if int(amount) <= 0:
          print("Cant bet negatives.")
          error[1] = "Amount must be a positive whole number."

      if not (team_num == "1" or team_num == "2" or team_num.lower() == match.t1.lower() or team_num.lower() == match.t2.lower()):
        print("Team num has to either be 1 or 2.")
        error[0] = f'Team number has to be "1", "2", "{match.t1}", or "{match.t2}".'
      else:
        if team_num.lower() == match.t1.lower():
          team_num = "1"
        elif team_num.lower() == match.t2.lower():
          team_num = "2"
      

      if not match.date_closed is None:
        await interaction.response.send_message("Betting has closed you cannot make a bet.")

      if error[0] is None:
        balance_left = user.get_balance() + bet.amount_bet - int(amount)
        if balance_left < 0:
          print("You have bet " + str(math.ceil(-balance_left)) + " more than you have.")
          error[1] = "You have bet " + str(math.ceil(-balance_left)) + " more than you have."

      if not error == [None, None]:
        errortext = ""
        if error[0] is not None:
          errortext += error[0]
          if error[1] is not None:
            errortext += "\n"
        if error[1] is not None:
          errortext += error[1]
        await interaction.response.send_message(errortext)
        return
      
      bet.amount_bet = int(amount)
      bet.team_num = int(team_num)


      embedd = await create_bet_embedded(bet, f"Edit Bet: {user.username}, {amount} on {bet.get_team()}.", session)
      
      inter = await interaction.response.send_message(embed=embedd)
      msg = await inter.original_message()

      await edit_all_messages(bet.message_ids, embedd)
      bet.message_ids.append((msg.id, msg.channel.id))
#bet edit modal end

  
#new match list autocomplete start
async def new_match_list_autocomplete(ctx: discord.AutocompleteContext):
  match_t_list = available_matches_name_code()
  if (user := get_from_db("User", ctx.interaction.user.id)) is None: return [match_t[0] for match_t in match_t_list if (ctx.value.lower() in match_t[0].lower())]
  active_bet_ids_matches = user.active_bet_ids_matches()
  auto_completes = [match_t[0] for match_t in match_t_list if (ctx.value.lower() in match_t[0].lower() and (match_t[1].code not in active_bet_ids_matches))]
  return auto_completes
#new match list autocomplete end

#bet list autocomplete start
async def bet_list_autocomplete(ctx: discord.AutocompleteContext):
  text = ctx.value.lower()
  bet_t_list = await current_bets_name_code(bot)
  auto_completes = [bet_t[0] for bet_t in bet_t_list if text in bet_t[0].lower()]
  if auto_completes == []:
    text.replace(",", "")
    text.replace(":", "")
    text_keywords = text.split(" ")
    all_bet_t_list = await all_bets_name_code(bot)
    all_bet_t_list.reverse()
    if len(text_keywords) == 0:
      return []
    for bet_t in all_bet_t_list:
      bet_detail = bet_t[0].lower()
      all_in = True
      for text_keyword in text_keywords:
        if text_keyword not in bet_detail:
          all_in = False
          break
      if all_in:
        auto_completes.append(bet_t[0])
        if len(auto_completes) == 25:
          break
        
  return auto_completes
#bet list autocomplete end

  
#user bet list autocomplete start
async def user_bet_list_autocomplete(ctx: discord.AutocompleteContext):
  bet_t_list = await current_bets_name_code(bot)
  auto_completes = [bet_t[0] for bet_t in bet_t_list if ctx.value.lower() in bet_t[0].lower() if ctx.interaction.user.id == bet_t[1].user_id]
  return auto_completes
#user bet list autocomplete end


#bet create start
@betscg.command(name = "create", description = "Create a bet.")
async def bet_create(ctx, match: Option(str, "Match you want to bet on.",  autocomplete=new_match_list_autocomplete)):
  user = get_from_list("user", ctx.author.id)
  if user is None:
    user = create_user(ctx.author.id, ctx.author.display_name)
    
  if (match := await user_from_autocomplete_tuple(ctx, available_matches_name_code(), match, "Match")) is None: return
  print(match)
    
  if match.date_closed is not None:
    await ctx.respond("Betting has closed.")
    return
  
  for bet_id in match.bet_ids:
    bet = get_from_list("bet", bet_id)
    if bet.user_id == user.code:
      await ctx.respond("You already have a bet on this match.")
      return

  bet_modal = BetCreateModal(match=match, user=user, title="Create Bet")
  await ctx.interaction.response.send_modal(bet_modal)
#bet create end


#bet cancel start
@betscg.command(name = "cancel", description = "Cancels a bet if betting is open on the match.")
async def bet_cancel(ctx, bet: Option(str, "Bet you want to cancel.", autocomplete=user_bet_list_autocomplete)):
  
  gen_msg = await ctx.respond("Cancelling bet...")
  if (bet := await user_from_autocomplete_tuple(ctx, await current_bets_name_code(bot), bet, "Bet")) is None: return
  
  match = get_from_list("match", bet.match_id)
  if (match is None) or (match.date_closed is not None):
    await gen_msg.edit_original_message(content="Match betting has closed, you cannot cancel the bet.")
    return
    
    
  try:
    match.bet_ids.remove(bet.code)
    replace_in_list("match", match.code, match)
    embedd = await create_match_embedded(match, "Placeholder")
    await edit_all_messages(match.message_ids, embedd)
  except:
    print(f"{bet.code} is not in match {match.code} bet ids {match.bet_ids}")
    
  
  await delete_all_messages(bet.message_ids)
  remove_from_active_ids(bet.user_id, bet.code)
  remove_from_list("bet", bet)
  user = get_from_list("user", bet.user_id)
  embedd = await create_bet_embedded(bet, f"Cancelled Bet: {user.username} with {bet.amount_bet} on {bet.get_team()}.")
  await gen_msg.edit_original_message(content="", embed=embedd)
#bet cancel end


#bet edit start
@betscg.command(name = "edit", description = "Edit a bet.")
async def bet_edit(ctx, bet: Option(str, "Bet you want to edit.", autocomplete=user_bet_list_autocomplete)):
  if (bet := await user_from_autocomplete_tuple(ctx, await current_bets_name_code(bot), bet, "Bet")) is None: return
  
  match = get_from_list("match", bet.match_id)
  if (match is None) or (match.date_closed is not None):
    await ctx.respond("Match betting has closed, you cannot edit the bet.")
    return
  
  user = get_from_list("user", bet.user_id)

  bet_modal = BetEditModal(bet=bet, match=match, user=user, title="Edit Bet")
  await ctx.interaction.response.send_modal(bet_modal)
#bet edit end


#bet find start
@betscg.command(name = "find", description = "Sends the embed of the bet.")
async def bet_find(ctx, bet: Option(str, "Bet you get embed of.", autocomplete=bet_list_autocomplete)):
  #list some old matches
  if (fbet := await user_from_autocomplete_tuple(None, await current_bets_name_code(bot), bet, "Bet")) is None: 
    if (fbet := await user_from_autocomplete_tuple(ctx, await all_bets_name_code(bot), bet, "Bet")) is None: return
  bet = fbet
  user = get_from_list("user", bet.user_id)
  embedd = await create_bet_embedded(bet, f"Bet: {user.username}, {bet.amount_bet} on {bet.get_team()}.")
  inter = await ctx.respond(embed=embedd)
  msg = await inter.original_message()
  bet.message_ids.append((msg.id, msg.channel.id))
  replace_in_list("bet", bet.code, bet)
#bet find end


#bet list start
@betscg.command(name = "list", description = "Sends embed with all bets. If type is full it sends the whole embed of each bet.")
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
    embedd = await create_bet_list_embedded("Bets:", bet_list, bot)
    await gen_msg.edit_original_message(content = "", embed=embedd)
    
  elif type == 1:
    #full
    for i, bet in enumerate(bet_list):
      user = get_from_list("user", bet.user_id)
      embedd = await create_bet_embedded(bet, f"Bet: {user.username}, {bet.amount_bet} on {bet.get_team()}.")
      if i == 0:
        inter = await ctx.respond(embed=embedd)
        msg = await inter.original_message()
      else:
        msg = await ctx.interaction.followup.send(embed=embedd)
      bet.message_ids.append((msg.id, msg.channel.id))
      replace_in_list("bet", bet.code, bet)
#bet list end
  
bot.add_application_command(betscg)
#bet end




#color start
colorscg = SlashCommandGroup(
  name = "color", 
  description = "Add, romove, rename, and recolor colors.",
  guild_ids = gid,
)

xkcd_colors = mcolors.XKCD_COLORS
#color xkcd autocomplete start
async def xkcd_picker_autocomplete(ctx: discord.AutocompleteContext): 
  val = ctx.value.lower() 
  colors = [x[5:].lower() for x in xkcd_colors.keys() if val in x]
  
  colors = colors[::-1]
  same = []
  start = []
  half_start = []
  contain = []
  val_words = val.split(" ")
  for color in colors:
    color_words = color.split(" ")
    if color.startswith(val):
      start.append(color)
    else:
      half = True
      for word in val_words:
        word_in = False
        for color_word in color_words:
          if color_word.startswith(word):
            word_in = True
        if not word_in:
          half = False
          break
      if half:
        half_start.append(color)
      elif color == val:
        same.append(color)
      else:
        contain.append(color)
    
  colors = same + start + half_start + contain
  colors = [color.capitalize() for color in colors]
  return colors
#color xkcd autocomplete end

  
#color list start
@colorscg.command(name = "list", description = "Lists all colors.")
async def color_list(ctx):
  print("getting list")
  colors = get_all_colors_key_hex()
  if len(colors) == 0:
    await ctx.respond("No colors found.")
    return
  
  font = ImageFont.truetype("font/whitneybold.otf", size=40)
  img = Image.new("RGBA", (800, (int((len(colors)+1)/2) * 100) + 100), (255,255,255,0))
  d = ImageDraw.Draw(img)
  for i, color in enumerate(colors):
    x = ((i % 2) * 350) + 50
    y = (int(i / 2) * 100) + 50
    hex = color[1]
    color_tup = hex_to_tuple(hex)
    d.text((x,y), color[0].capitalize(), fill=(*color_tup,255), font=font)
  with BytesIO() as image_binary:
    gen_msg = await ctx.respond("Generating color list...")
    img.save(image_binary, 'PNG')
    image_binary.seek(0)
    await gen_msg.edit_original_message(content = "", file=discord.File(fp=image_binary, filename='image.png'))
#color list end

  
#color add start
@colorscg.command(name = "add", description = "Adds the color to color list.")
async def color_add(ctx, custom_color_name:Option(str, "Name of color you want to add.", required=False), hex: Option(str, "Hex color code of new color. The 6 numbers/letters.", required=False), xkcd_color_name: Option(str, "Name of color you want to add.", autocomplete=xkcd_picker_autocomplete, required=False)):
  if xkcd_color_name is not None:
    if hex is not None:
      await ctx.respond("You can't add a hex code and a xkcd color name.")
      return
    hex = xkcd_colors[f"xkcd:{xkcd_color_name.lower()}"]
    if custom_color_name is not None:
      xkcd_color_name = custom_color_name
    await ctx.respond(add_color(xkcd_color_name, hex), ephemeral = True)
  elif custom_color_name is not None and hex is not None:
    await ctx.respond(add_color(custom_color_name, hex), ephemeral = True)
  else:
    await ctx.respond("Please enter a name and hex code or a xkcd color.", ephemeral = True)
#color add end

  
#color recolor start
@colorscg.command(name = "recolor", description = "Recolors the color.")
async def color_recolor(ctx, color_name: Option(str, "Name of color you want to replace color of.", autocomplete=color_picker_autocomplete), hex: Option(str, "Hex color code of new color. The 6 numbers/letters.")):
  await ctx.respond(recolor_color(color_name, hex), ephemeral = True)
#color recolor end

  
#color remove start
@colorscg.command(name = "remove", description = "Removes the color from color list.")
async def color_remove(ctx, color_name: Option(str, "Name of color you want to remove.", autocomplete=color_picker_autocomplete)):
  await ctx.respond(remove_color(color_name)[0], ephemeral = True)
#color remove end

  
#color rename start
@colorscg.command(name = "rename", description = "Renames the color.")
async def color_rename(ctx, old_color_name: Option(str, "Name of color you want to rename.", autocomplete=color_picker_autocomplete), new_color_name: Option(str, "New name of color.")):
  await ctx.respond(rename_color(old_color_name, new_color_name), ephemeral = True)
#color rename end

  
bot.add_application_command(colorscg)
#color end



    
#profile start
profile = SlashCommandGroup(
  name = "profile", 
  description = "Change your settings.",
  guild_ids = gid,
)


  
#profile color start
@profile.command(name = "color", description = "Sets the color of embeds sent with your username.")
async def profile_color(ctx, color_name: Option(str, "Name of color you want to set as your profile color.", autocomplete=color_picker_autocomplete)):
  if (color_hex := get_color(color_name)) is None:
    await ctx.respond(f"Color {color_name} not found. You can add a color by using the command /color add")
    return
  if (user := await get_user_from_member(ctx, ctx.author)) is None: return
  user.color = color_hex
  replace_in_list("user", user.code, user)
  await ctx.respond(f"Profile color is now {color_name}.")
#profile color end

bot.add_application_command(profile)
#profile end


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
]

@graph.command(name = "balance", description = "Gives a graph of value over time. No value in type gives you the current season.")
async def graph_balances(ctx,
  type: Option(int, "What type of graph you wany to make.", choices = balance_choices, default = 0, required = False), 
  amount: Option(int, "How many you want to look back. For last only.", default = None, required = False),
  user: Option(discord.Member, "User you want to get balance of.", default = None, required = False),
  compare: Option(str, "Users you want to compare. For compare only", autocomplete=multi_user_list_autocomplete, default = None, required = False)):
  
  if (user is not None) and (compare is not None):
    await ctx.respond("You can't use compare and user at the same time.")
    return
  if (user is None) and (compare is None):
    await ctx.respond("You must have either compare or user.")
    return
    
  if compare is None:
    if (user := await get_user_from_member(ctx, user)) is None: return
    if amount is not None:
      if amount > len(user.balances):
        amount = len(user.balances)
      if amount <= 1:
        await ctx.respond("Amount needs to be higher.")
      graph_type = amount
    else:
      if type == 0:
        graph_type = "current"
      elif type == 1:
        graph_type = "all"
      else:
        await ctx.respond("Not a valid type.")
        return

    with BytesIO() as image_binary:
      gen_msg = await ctx.respond("Generating graph...")
      image = user.get_graph_image(graph_type)
      if isinstance(image, str):
        await gen_msg.edit_original_message(content = image)
        return
      image.save(image_binary, 'PNG')
      image_binary.seek(0)
      await gen_msg.edit_original_message(content = "", file=discord.File(fp=image_binary, filename='image.png'))
    return
  

  usernames_split = compare.split(" ")
  
  users = usernames_to_users(compare)

  
  if len(users) == 1:
    await ctx.respond("You need to compare more than one user.")
    return

  
  usernames = " ".join([user.username for user in users])

  for username_word in usernames_split:
    if username_word not in usernames:
      await ctx.respond(f"User {username_word} not found.")
      return

  print(users)

  

  if amount is not None:
    highest_length = 0
    highest_length = len(get_all_unique_balance_ids(users))
    if amount > highest_length:
      amount = highest_length
      if amount <= 1:
        await ctx.respond("Amount needs to be higher.")
    graph_type = amount
  else:
    if type == 0:
      graph_type = "current"
    elif type == 1:
      graph_type = "all"
    else:
      await ctx.respond("Not a valid type.")
      return

  with BytesIO() as image_binary:
    gen_msg = await ctx.respond("Generating graph...")
    image = get_multi_graph_image(users, graph_type)
    if isinstance(image, str):
      await gen_msg.edit_original_message(content = image)
      return
    image.save(image_binary, 'PNG')
    image_binary.seek(0)
    await gen_msg.edit_original_message(content = "", file=discord.File(fp=image_binary, filename='image.png'))
    
  
#graph balance end

bot.add_application_command(graph)
#graph end



#leaderboard start
@bot.slash_command(name = "leaderboard", description = "Gives leaderboard of balances.", guild_ids = gid)
async def leaderboard(ctx):
  embedd = await create_leaderboard_embedded()
  await ctx.respond(embed=embedd)
#leaderboard end


  
#log start
@bot.slash_command(name = "log", description = "Shows the last x amount of balance changes (awards, bets, etc)", guild_ids = gid)
async def log(ctx, amount: Option(int, "How many balance changes you want to see."), user: Option(discord.Member, "User you want to check log of (defaulted to you).", default = None, required = False)):

  if (user := await get_user_from_member(ctx, user)) is None: return
  
  if amount <= 0:
    await ctx.respond("Amount has to be greater than 0.")
    return
    
  gen_msg = await ctx.respond("Generating log...")
  
  embedds = user.get_new_balance_changes_embeds(amount)
  if embedds is None:
    await gen_msg.edit_original_message(content = "No log generated.")
    return

  await gen_msg.edit_original_message(content="", embed=embedds[0])
  for embedd in embedds[1:]:
    await ctx.channel.send(embed=embedd)
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
  user.loans.append((50, get_date(), None))
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
    new_loan[2] = get_date()
    new_loan = tuple(new_loan)


    index = user.loans.index(loan)
    user.loans[index] = new_loan
  replace_in_list("user", user.code, user)
  await ctx.respond(f"You have paid off {len(loans)} loan(s)")
#loan pay end

bot.add_application_command(loan)
#loan end


#match start
matchscg = SlashCommandGroup(
  name = "match", 
  description = "Create, edit, and view matches.",
  guild_ids = gid,
)

#match create modal start
class MatchCreateModal(Modal):
  
  def __init__(self, balance_odds=0, *args, **kwargs) -> None:
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
    
    
    if odds_combined.count(" ") > 1:
      odds_combined.strip(" ")
      
    splits = [" ", "/", "\\", ";", ":", ",", "-", "_", "|"]
    for spliter in splits:
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
      odds1 = team_one_old_odds - 1
      odds2 = team_two_old_odds - 1
      
      oneflip = 1 / odds1
      
      percentage1 = (math.sqrt(odds2/oneflip))
      
      team_one_odds = roundup(odds1 / percentage1) + 1
      team_two_odds = roundup(odds2 / percentage1) + 1
    else:
      team_one_odds = team_one_old_odds
      team_two_odds = team_two_old_odds
      
    print(team_one_odds, team_two_odds)
    
    code = get_unique_code("Match")
  
    color = code[:6]
    match = Match(team_one, team_two, team_one_old_odds, team_two_old_odds, team_one_odds, team_two_odds, tournament_name, betting_site, interaction.user.id, get_date(), color, code)

    
    
    #date_formatted = cmatch.date_created.strftime("%m/%d/%Y %H:%M:%S")
    
    embedd = await create_match_embedded(match, f"New Match: {team_one} vs {team_two}, {team_one_odds} / {team_two_odds}.")

    if (channel := await bot.fetch_channel(get_file("match_channel_id"))) == interaction.channel:
      inter = await interaction.response.send_message(embed=embedd)
      msg = await inter.original_message()
    else:
      msg = await channel.send(embed=embedd)
      await interaction.response.send_message(f"Match created in {channel.mention}.", ephemeral = True)
      
    match.message_ids.append((msg.id, msg.channel.id))
    add_to_list("match", match)
#match create modal end

#match edit modal start
class MatchEditModal(Modal):
  
  def __init__(self, match, balance_odds, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    
    self.match = match
    self.balance_odds = balance_odds
    
    self.add_item(InputText(label="Enter team one name.", placeholder=match.t1, min_length=1, max_length=100, required=False))
    self.add_item(InputText(label="Enter team two name.", placeholder=match.t2, min_length=1, max_length=100, required=False))
    
    self.add_item(InputText(label="Enter odds. Team 1 odds/Team 2 odds.", placeholder=f"{match.t1oo}/{match.t2oo}", min_length=1, max_length=12, required=False))
    self.add_item(InputText(label="Enter tournament name.", placeholder=match.tournament_name, min_length=1, max_length=300, required=False))
    
    self.add_item(InputText(label="Enter odds source.", placeholder=match.odds_source, min_length=1, max_length=100, required=False))

  
  async def callback(self, interaction: discord.Interaction):
    team_one = self.children[0].value.strip()
    if team_one == "":
      team_one = self.match.t1
    team_two = self.children[1].value.strip()
    if team_two == "":
      team_two = self.match.t2
    odds_combined = self.children[2].value.strip()
    if odds_combined == "":
      odds_combined = f"{self.match.t1oo}/{self.match.t2oo}"
    tournament_name = self.children[3].value.strip()
    if tournament_name == "":
      tournament_name = self.match.tournament_name
    betting_site = self.children[4].value.strip()
    if betting_site == "":
      betting_site = self.match.odds_source
    
    
    if odds_combined.count(" ") > 1:
      odds_combined.strip(" ")
      
    splits = [" ", "/", "\\", ";", ":", ",", "-", "_", "|"]
    for spliter in splits:
      if odds_combined.count(spliter) == 1:
        team_one_old_odds, team_two_old_odds = "".join(_ for _ in odds_combined if _ in f".1234567890{spliter}").split(spliter)
        break
    else:
      await interaction.response.send_message(f"Odds are not valid. Odds must be [odds 1]/[odds 2].")
      return
      
    if (to_float(team_one_old_odds) is None) or (to_float(team_two_old_odds) is None): 
      await interaction.response.send_message(f"Odds are not valid. Odds must be valid decimal numbers.")
      return
    
    team_one_old_odds = to_float(team_one_old_odds)
    team_two_old_odds = to_float(team_two_old_odds)
    if team_one_old_odds <= 1 or team_two_old_odds <= 1:
      await interaction.response.send_message(f"Odds must be greater than 1.")
      return
    if self.balance_odds == 0:
      odds1 = team_one_old_odds - 1
      odds2 = team_two_old_odds - 1
      
      oneflip = 1 / odds1
      
      percentage1 = (math.sqrt(odds2/oneflip))
      
      team_one_odds = roundup(odds1 / percentage1) + 1
      team_two_odds = roundup(odds2 / percentage1) + 1
    else:
      team_one_odds = team_one_old_odds
      team_two_odds = team_two_old_odds
      
    match = self.match
    match.t1 = team_one
    match.t2 = team_two
    match.t1oo = team_one_old_odds
    match.t2oo = team_two_old_odds
    match.t1o = team_one_odds
    match.t2o = team_two_odds
    match.tournament_name = tournament_name
    match.odds_source = betting_site

    embedd = await create_match_embedded(match, f"Edited Match: {team_one} vs {team_two}, {team_one_odds} / {team_two_odds}.")

    inter = await interaction.response.send_message(embed=embedd)
    msg = await inter.original_message()
    await edit_all_messages(match.message_ids, embedd)
    match.message_ids.append((msg.id, msg.channel.id))
    replace_in_list("match", match.code, match)
#match edit modal end

    
#tournament autocomplete start (unused)
async def tournament_list_autocomplete(ctx: discord.AutocompleteContext):
  return get_last_tournament_name(5)
#tournament autocomplete end (unused)

#match list autocomplete start
async def match_list_autocomplete(ctx: discord.AutocompleteContext):
  text = ctx.value.lower()
  match_t_list = current_matches_name_code()
  auto_completes = [match_t[0] for match_t in match_t_list if (text in match_t[0].lower())]
  if auto_completes == []:
    text.replace(",", "")
    text.replace(":", "")
    text_keywords = text.split(" ")
    all_match_t_list = all_matches_name_code()
    all_match_t_list.reverse()
    if len(text_keywords) == 0:
      return []
    for match_t in all_match_t_list:
      match_detail = match_t[0].lower()
      all_in = True
      for text_keyword in text_keywords:
        if text_keyword not in match_detail:
          all_in = False
          break
      if all_in:
        auto_completes.append(match_t[0])
        if len(auto_completes) == 25:
          break
        
  return auto_completes
#match list autocomplete end
  
#match current list autocomplete start
async def match_current_list_autocomplete(ctx: discord.AutocompleteContext):
  text = ctx.value.lower()
  match_t_list = current_matches_name_code()
  auto_completes = [match_t[0] for match_t in match_t_list if (text in match_t[0].lower())]
        
  return auto_completes
#match current list autocomplete end

#match available list autocomplete start
async def match_available_list_autocomplete(ctx: discord.AutocompleteContext):
  text = ctx.value.lower()
  match_t_list = available_matches_name_code()
  auto_completes = [match_t[0] for match_t in match_t_list if (text in match_t[0].lower())]
        
  return auto_completes
#match available list autocomplete end
  
#match bet free available list autocomplete start
async def match_bet_free_available_list_autocomplete(ctx: discord.AutocompleteContext):
  text = ctx.value.lower()
  match_t_list = available_matches_name_code()
  auto_completes = [match_t[0] for match_t in match_t_list if ((text in match_t[0].lower()) and (match_t[1].bet_ids == []))]
        
  return auto_completes
  

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
  match = ctx.options["match"]
  if match is None: return []
  if (match := await user_from_autocomplete_tuple(None, current_matches_name_code(), match, "Match")) is None: return []
  auto_completes = [match.t1, match.t2]
  return auto_completes
#match match team autocomplete end

  
#match winner autocomplete start
async def match_winner_list_autocomplete(ctx: discord.AutocompleteContext):
  match = ctx.options["match"]
  if match is None: return []
  if (match := await user_from_autocomplete_tuple(None, all_matches_name_code(), match, "Match")) is None: return []
  
  strin = "None"
  if match.t1 == "None" or match.t2 == "None":
    strin = "Set winner to none"
  auto_completes = [match.t1, match.t2, strin]
  
  return auto_completes
#match winner autocomplete end
  

#match bets start
@matchscg.command(name = "bets", description = "What bets.")
async def match_bets(ctx, match: Option(str, "Match you want bets of.", autocomplete=match_list_autocomplete), type: Option(int, "If type is full it sends the whole embed of each match.", choices = list_choices, default = 0, required = False)):
  #to do list some old ones
  
  if (fmatch := await user_from_autocomplete_tuple(None, current_matches_name_code(), match, "Match")) is None:
    if (fmatch := await user_from_autocomplete_tuple(ctx, all_matches_name_code(), match, "Match")) is None: return
  match = fmatch

  

  bet_ids = match.bet_ids
  bet_list = []
  for bet_id in bet_ids:
    bet_list.append(get_from_list("bet", bet_id))

  if len(bet_list) == 0:
    await ctx.respond(f"No bets on match {match.t1} vs {match.t2}.")
    return
  if type == 0:
    #short
    gen_msg = await ctx.respond("Generating bets...")
    embedd = await create_bet_list_embedded(f"Bets on Match:", bet_list, bot)
    await gen_msg.edit_original_message(content = "", embed=embedd)
    
  elif type == 1:
    #full
    for i, bet in enumerate(bet_list):
      user = get_from_list("user", bet.user_id)
      embedd = await create_bet_embedded(bet, f"Bet: {user.username}, {bet.amount_bet} on {bet.get_team()}.")
      if i == 0:
        inter = await ctx.respond(embed=embedd)
        msg = await inter.original_message()
      else:
        msg = await ctx.interaction.followup.send(embed=embedd)
      bet.message_ids.append((msg.id, msg.channel.id))
      replace_in_list("bet", bet.code, bet)
#match bets end


#match betting start
@matchscg.command(name = "betting", description = "Open and close betting.")
async def match_betting(ctx, type: Option(int, "Set to open or close", choices = open_close_choices), match: Option(str, "Match you want to open/close.", autocomplete=match_open_close_list_autocomplete)):

  if (match := await user_from_autocomplete_tuple(ctx, current_matches_name_code(), match, "Match")) is None: return

  #if already on dont do anything complex
    
  if type == 0:
    match.date_closed = None
    await ctx.respond(f"{match.t1} vs {match.t2} betting has opened.")
  else:
    match.date_closed = get_date()
    await ctx.respond(f"{match.t1} vs {match.t2} betting has closed.")
  replace_in_list("match", match.code, match)
  embedd = await create_match_embedded(match, "Placeholder")
  await edit_all_messages(match.message_ids, embedd)
#match betting end
  
  
#match create start
@matchscg.command(name = "create", description = "Create a match.")
async def match_create(ctx, balance_odds: Option(int, "balance the odds? Defualt is Yes.", choices = yes_no_choices, default=0, required=False)):
    
  match_modal = MatchCreateModal(balance_odds=balance_odds, title="Create Match")
  await ctx.interaction.response.send_modal(match_modal)
#match create end


#match delete start
@matchscg.command(name = "delete", description = "Delete a match. Can only be done if betting is open.")
async def match_delete(ctx, match: Option(str, "Match you want to delete.", autocomplete=match_available_list_autocomplete)):
  
  if (match := await user_from_autocomplete_tuple(ctx, available_matches_name_code(), match, "Match")) is None: return
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
  embedd = await create_match_embedded(bet, f"Deleted Match: {match.t1} vs {match.t2}, {match.t1o} / {match.t2o}, and all bets on the match.")
  await gen_msg.edit_original_message(content="", embed=embedd)
#match delete end
  

#match find start
@matchscg.command(name = "find", description = "Sends the embed of the match.")
async def match_find(ctx, match: Option(str, "Match you want embed of.", autocomplete=match_list_autocomplete)):
  #to do list some old ones
  if (fmatch := await user_from_autocomplete_tuple(None, current_matches_name_code(), match, "Match")) is None:
    if (fmatch := await user_from_autocomplete_tuple(ctx, all_matches_name_code(), match, "Match")) is None: return
  match = fmatch
  embedd = await create_match_embedded(match, f"Match: {match.t1} vs {match.t2}, {match.t1o} / {match.t2o}.")
  inter = await ctx.respond(embed=embedd)
  msg = await inter.original_message()
  
  match.message_ids.append((msg.id, msg.channel.id))
  replace_in_list("match", match.code, match)
#match find end


#match edit start
@matchscg.command(name = "edit", description = "Edit a match.")
async def match_edit(ctx, match: Option(str, "Match you want to edit.", autocomplete=match_bet_free_available_list_autocomplete), balance_odds: Option(int, "balance the odds? Defualt is Yes.", choices = yes_no_choices, default=0, required=False)):
  if (match := await user_from_autocomplete_tuple(ctx, available_matches_name_code(), match, "Match")) is None: return
  if match.bet_ids != []:
    await ctx.respond(f"Match must have no bets. You must delete the bets before editing the match. (To delete other users bets type in their bet code).")
    return
  await ctx.interaction.response.send_modal(MatchEditModal(match=match, balance_odds=balance_odds, title="Edit Match"))
#match edit end


#match list start
@matchscg.command(name = "list", description = "Sends embed with all matches. If type is full it sends the whole embed of each match.")
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
      embedd = await create_match_embedded(match, f"Match: {match.t1} vs {match.t2}, {match.t1o} / {match.t2o}.")
      if i == 0:
        inter = await ctx.respond(embed=embedd)
        msg = await inter.original_message()
      else:
        msg = await ctx.interaction.followup.send(embed=embedd)
      match.message_ids.append((msg.id, msg.channel.id))
      replace_in_list("match", match.code, match)
#match list end
  
  
#match winner start
@matchscg.command(name = "winner", description = "Set winner of match.")
async def match_winner(ctx, match: Option(str, "Match you want to set winner of.", autocomplete=match_current_list_autocomplete), team: Option(str, "Team to set to winner.", autocomplete=match_team_list_autocomplete)):
  
  if (match := await user_from_autocomplete_tuple(ctx, current_matches_name_code(), match, "Match")) is None: return
  team.strip()
  if (team == "1") or (team == match.t1):
    team = 1
  elif (team == "2") or (team == match.t2):
    team = 2
  else:
    await ctx.respond(f"Invalid team name of {team} please enter {match.t1} or {match.t2}.")
    return
  
  if int(match.winner) != 0:
    await ctx.respond(f"Winner has already been set to {match.winner_name()}")
    return

  match.winner = team
  time = get_date()
  
  match.date_winner = time
  if match.date_closed is None:
    match.date_closed = time
    
  m_embedd = await create_match_embedded(match, "Placeholder")
  
  odds = 0.0
  #change when autocomplete
  if team == 1:
    odds = match.t1o
    await ctx.respond(f"Winner has been set to {match.t1}.")
  else:
    odds = match.t2o
    await ctx.respond(f"Winner has been set to {match.t2}.")

  msg_ids = []
  bet_user_payouts = []
  date = get_date()
  for bet_id in match.bet_ids:
    bet = get_from_list("bet", bet_id)
    if not bet is None:
      #to do print out embedds of bets
      bet.winner = int(match.winner)
      payout = -bet.amount_bet
      if bet.team_num == team:
        payout += bet.amount_bet * odds
      user = get_from_list("user", bet.user_id)
      remove_from_active_ids(user, bet.code)
      add_balance_user(user, payout, "id_" + str(bet.code), date)
      
      replace_in_list("bet", bet.code, bet)
      
      embedd = await create_bet_embedded(bet, "Placeholder")
      msg_ids.append((bet.message_ids, embedd))
      bet_user_payouts.append((bet, user, payout))
    else:
      print(f"where the bet_id from {bet_id}")
  replace_in_list("match", match.code, match)


  embedd = await create_payout_list_embedded(f"Payouts of {match.t1} vs {match.t2}:", match, bet_user_payouts)
  await ctx.interaction.followup.send(embed=embedd)

  await edit_all_messages(match.message_ids, m_embedd)
  [await edit_all_messages(tup[0], tup[1]) for tup in msg_ids]
#match winner end


#match reset start
@matchscg.command(name = "reset", description = "Change winner or go back to no winner.")
async def match_winner(ctx, match: Option(str, "Match you want to reset winner of.", autocomplete=match_list_autocomplete), team: Option(str, "Team to set to winner.", autocomplete=match_winner_list_autocomplete), new_date: Option(int, "Do you want to reset the winner set date?", choices = yes_no_choices)):
  if (match := await user_from_autocomplete_tuple(ctx, all_matches_name_code(), match, "Match")) is None: return
  if new_date == 0:
    new_date = True
  else:
    new_date = False
  
  team.strip()
  if (team == "1") or (team == match.t1):
    team = 1
  elif (team == "2") or (team == match.t2):
    team = 2
  elif (team == "0") or (team == "None") or (team == "Set winner to none"):
    team = 0
  else:
    await ctx.respond(f"Invalid team name of {team} please enter {match.t1}, {match.t2}, or None.")
    return
  
  if int(match.winner) == team:
    await ctx.respond(f"Winner has already been set to {match.winner_name()}")
    return
    
  gen_msg = await ctx.respond("Reseting match...")
  
  match.winner = team
  if new_date:
    match.date_winner = get_date()
  
  if match.date_closed is None:
    match.date_closed = match.date_winner
    
  m_embedd = await create_match_embedded(match, "Placeholder")

  for bet_id in match.bet_ids:
    bet = get_from_list("bet", bet_id)
    user = get_from_list("user", bet.user_id)
    user.remove_balance_id(f"id_{bet.code}")

  if match.winner == 0:
    await gen_msg.edit_original_message("Winner has been set to None.")
    replace_in_list("match", match.code, match)
    return
  
  odds = 0.0
  #change when autocomplete
  if team == 1:
    odds = match.t1o
    await gen_msg.edit_original_message(f"Winner has been set to {match.t1}.")
  else:
    odds = match.t2o
    await gen_msg.edit_original_message(f"Winner has been set to {match.t2}.")

  msg_ids = []
  users = []
  date = match.date_winner
  for bet_id in match.bet_ids:
    bet = get_from_list("bet", bet_id)
    if not bet is None:
      #to do print out embedds of bets
      bet.winner = int(match.winner)
      payout = -bet.amount_bet
      if bet.team_num == team:
        payout += bet.amount_bet * odds
      user = get_from_list("user", bet.user_id)
      remove_from_active_ids(user, bet.code)
      add_balance_user(user, payout, "id_" + str(bet.code), date)

      replace_in_list("bet", bet.code, bet)

      embedd = await create_bet_embedded(bet, "Placeholder")
      msg_ids.append((bet.message_ids, embedd))
      users.append(user.code)
    else:
      print(f"where the bet_id from {bet_id}")
  replace_in_list("match", match.code, match)

  no_same_list_user = []
  [no_same_list_user.append(x) for x in users if x not in no_same_list_user]
  for user in no_same_list_user:
    embedd = await create_user_embedded(user)
    await ctx.send(embed=embedd)

  await edit_all_messages(match.message_ids, m_embedd)
  [await edit_all_messages(tup[0], tup[1]) for tup in msg_ids]
#match reset end
  
  
bot.add_application_command(matchscg)
#match end


#backup
@bot.command()
async def backup_db(ctx):
  backup()
  
#hidden command
@bot.command()
async def hide_from_leaderboard(ctx):
  if (user := await get_user_from_member(None, ctx.author)) is None: return
  user.hidden = not user.hidden
  replace_in_list("user", user.code, user)
  print(user.hidden)




#season reset command
@bot.command()
async def reset_season(ctx, name):
  # to do make the command also include season name
  users = get_all_objects("user")

  code = all_user_unique_code("reset_", users)
  date = get_date()
  name = f"reset_{code}_{name}"
  for user in users:
    user.balances.append((name, Decimal(500), date))
    replace_in_list("user", user.code, user)
  await ctx.send(f"Season reset. New season {name} has sarted.")

#debug
@bot.command()
async def debug(ctx, *args):
  await ctx.send("Not valid command.")

@bot.command()
async def clean_match_bet_ids_without_bet(ctx):
  return
  matches = get_all_objects("match")
  bets = get_all_objects("bet")
  for match in matches:
    for bet_id in match.bet_ids:
      in_bet = 0
      for bet in bets:
        if bet.code == bet_id:
          in_bet += 1

      if in_bet != 1:
        print(bet_id, in_bet, match.code)
        match.bet_ids.remove(bet_id)
        replace_in_list("match", match.code, match)
  print("end")

@bot.command()
async def add_team_names(ctx):
  return
  bets = get_all_objects("bet")
  for bet in bets:
    match = get_from_list("match", bet.match_id)
    bet.t1 = match.t1
    bet.t2 = match.t2
    bet.tournament_name = match.tournament_name
    replace_in_list("bet", bet.code, bet)
  print("done")
  
# debug command
@bot.command()
async def check_balance_order(ctx):
  #check if the order of user balance and the order of timer in balances[2] are the same
  users = get_all_objects("user")
  for user in users:
    sorted = user.balances.copy()
    sorted.sort(key=lambda x: x[2])
    if sorted != user.balances:
      print(f"{user.code} balance order is wrong")
  print("check order done")

    
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
    for bal in user.balances:

      user.balances[user.balances.index(bal)] = (user.balances[user.balances.index(bal)][0], round(user.balances[user.balances.index(bal)][1], 5), user.balances[user.balances.index(bal)][2])

    replace_in_list("user", user.code, user)


# debug command
@bot.command()
async def delete_last_bal(ctx):
  return
  users = get_all_objects("user")
  for user in users:
    print(user.balances)
    if type(user.balances[-1][1]) == tuple:
      user.balances.pop()
      print(user.balances)
      replace_in_list("user", user.code, user)

      
# debug command
@bot.command()
async def add_var(ctx):
  return
  users = get_all_objects("user")
  reset_dict = {}
  for user in users:
    for i, bal in enumerate(user.balances):
      bet_id, amount, time = bal
      bet_id = bet_id.split("_")[0] + "_" + bet_id.split("_")[-1]
      if bet_id.startswith("award_"):
        code = user.get_unique_code("award_")
        bet_id = bet_id[:bet_id.index("award_")+6] + code + "_" + bet_id[bet_id.index("award_")+6:]
        print(bet_id)
        user.balances[i] = (bet_id, amount, time)
        
      elif bet_id.startswith("reset_"):
        if bet_id in reset_dict:
          bet_id = reset_dict[bet_id]
        else:
          code = user.get_unique_code("reset_")
          #insert code after reset_
          old_bet_id = bet_id
          bet_id = bet_id[:bet_id.index("reset_")+6] + code + "_" + bet_id[bet_id.index("reset_")+6:]
          reset_dict[old_bet_id] = bet_id
        print(bet_id)
        user.balances[i] = (bet_id, amount, time)
    replace_in_list("user", user.code, user)
  print("done add var")


# debug command
@bot.command()
async def add_diff(ctx):
  return
  users = get_all_objects("user")
  for user in users:
    last = None
    for i, bal in enumerate(user.balances):
      if len(bal) == 3:
        diff = None
        if last is None or bal[0] == "start" or bal[0].startswith("reset_"):
          diff = None
          user.balances[i] = (bal[0], round(bal[1], 5), None, bal[2])
        else:
          diff = bal[1] - last
          user.balances[i] = (bal[0], round(bal[1], 5), round(diff, 5), bal[2])
        last = bal[1]
    
    x = Decimal(0)
    good = True
    for bal in user.balances:
      if bal[2] is None:
        x = Decimal(bal[1])
        continue 
      x += bal[2]
      if x != bal[1]:
        print(f"{user.username} balanceorder is wrong. {bal}: {x} != {bal[1]}")
        good = False
    if good:
      print(f"{user.username} balanceorder is good")
    else:
      print(f"{user.username} balanceorder is wrong")
    print([(bal[0], bal[1], bal[2]) for bal in user.balances])
    #replace_in_list("user", user.code, user)

  print("done")
  return

# debug command
@bot.command()
async def test_get_object(ctx):
  return
  user = get_from_list("user", ctx.author.id)
  replace_in_list("user", user.code, user)
  print("done")

@bot.command()
async def find_common_ids(ctx):
  return
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
    for bal in user.balances:
      if user.balances[user.balances.index(bal)][0] == "reset 1":
        user.balances[user.balances.index(bal)] = ("reset_2022 Stage 1" , user.balances[user.balances.index(bal)][1], user.balances[user.balances.index(bal)][2])

    replace_in_list("user", user.code, user)


token = get_setting("discord_token")
#print(f"discord: {token}")
bot.run(token)
