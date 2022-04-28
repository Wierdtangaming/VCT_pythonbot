
from Match import Match
from Bet import Bet
from User import User
import discord
from dbinterface import get_from_db, get_condition_db
from sqlalchemy import literal
from sqlaobjs import Session


def ambig_to_obj(ambig, prefix, session=None):
  if isinstance(ambig, int) or isinstance(ambig, str):
    obj = get_from_db(prefix, ambig, session)
  elif isinstance(ambig, discord.Member):
    obj = get_from_db(prefix, ambig.id, session)
  elif isinstance(ambig, User) or isinstance(ambig, Match) or isinstance(ambig, Bet):
    obj = ambig
  else:
    obj = None
    print(ambig, type(ambig))
  return obj

def get_user_from_at(id, session=None):
  uid = id.replace("<", "")
  uid = uid.replace(">", "")
  uid = uid.replace("@", "")
  uid = uid.replace("!", "")
  if uid.isdigit():
    return get_user_from_id(int(uid), session)
  else:
    return None

def get_user_from_id(id, session=None):
  return get_from_db("User", id, session)
  

def id_to_metion(id):
  return f"<@!{id}>"


  
async def get_user_from_ctx(ctx, user, session=None):
  if user is None:
    user = ctx.author
  user = get_from_db("User", user.id, session)
  if user is None:
    await ctx.respond("User not found. To create an account do /balance", ephemeral = True)
  return user


async def user_from_autocomplete_tuple(ctx, t_list, text, prefix, session=None):
  have ambig test if t_list is a list of name_objs or objs
  objs = [t[1] for t in t_list if text == t[0]]
  print(objs)
  if len(objs) >= 2:
    print("More than one of text found", objs)
    if ctx is not None:
      await ctx.respond(f"Error please @pig. Try typing in code instead.")
      #2 with the same name
    return None
  if len(objs) == 0:
    obj = get_from_db(prefix, text, session)
  else:
    obj = objs[0]
    
  if obj == [] or obj is None:
    if ctx is not None:
      await ctx.respond(f"{prefix.capitalize()} ID not found.", ephemeral = True)
    return None
  return obj

async def get_member_from_id(guild, id):
  member = guild.get_member(id)
  if member is None:
    member = await guild.fetch_member(id)
  return member


def get_user_from_username(username, session=None):
  return get_condition_db("User", User.username == username, session)


def usernames_to_users(usernames, session=None):
  return get_condition_db("User", literal(usernames).contains(User.username), session)


def filter_names(value, ambig):
  have ambig test if it is a list of objs or names
  if len(ambig) == 0:
    return []
  if isinstance(ambig[0], str):
    names = ambig
  elif isinstance(ambig[0], User):
    
  
  value = value.lower()
  value.replace(",", "")
  value_keywords = value.split(" ")
  if len(value_keywords) == 0:
    return [names]
  new_names = []
  for name in names:
    lower_name = name.lower()
    all_in = True
    for value_keyword in value_keywords:
      if value_keyword not in lower_name:
        all_in = False
        break
    if all_in:
      new_names.append(name)
      if len(new_names) == 25:
        break
  return new_names


def add_time_name_objs(name_objs):
  new_name_objs = []
  names = [name for name, _ in name_objs]
  for name_obj in name_objs:
    if names.count(name_obj[0]) == 2:
      new_name_objs.append((f"{name_obj[0]}, {name_obj[1].date_created.strftime('%m/%d')}", name_obj[1]))
    else:
      new_name_objs.append(name_obj)
  return new_name_objs


def shorten_match_name(match):
  if match.winner != 0:
    prefix = "Concluded: "
    shortened_prefix = "Con: "
  else:
    prefix = ""
    shortened_prefix = ""
  
  
  s = f"{prefix}{match.t1} vs {match.t2}, {match.tournament_name}"
  if len(s) >= 95:
    s = f"{shortened_prefix}{match.t1} vs {match.t2}, {match.tournament_name}"
    if len(s) >= 95:
      s = f"{shortened_prefix}{match.t1}/{match.t2}, {match.tournament_name}"
      if len(s) >= 95:
        tsplit = match.tournament_name.split(" ")[0]
        s = f"{shortened_prefix}{match.t1}/{match.t2}, {tsplit}"
        if len(s) >= 95:
          s = s[:95]
  return s

def shorten_bet_name(bet, session=None):
  if session is None:
    with Session() as session:
      return shorten_bet_name(bet, session)
  if bet.winner != 0:
    prefix = "Paid out: "
    shortened_prefix = "Paid: "
  else:
    prefix = ""
    shortened_prefix = ""
  user = bet.user
  s = f"{prefix}{user.username}: {bet.amount_bet} on {bet.get_team()}"
  if len(s) >= 100:
    s = f"{shortened_prefix}{user.username}: {bet.amount_bet} on {bet.get_team()}"
    if len(s) >= 100:
      s = s[:100]
  return s


def get_all_bets(session=None, show_hidden=False):
  if show_hidden:
    cond = (Bet.winner == 0)
  else:
    cond = (Bet.winner == 0 & Bet.hidden == False)
  return get_condition_db("Bet", cond, session)

def get_all_user_bets(user, session=None):
  return get_condition_db("Bet", Bet.user_id == user.id, session)

def get_open_user_bets(user, session=None):
  if session is None:
    with Session() as session:
      return get_open_user_bets(user, session)
  return [bet for bet in get_condition_db("Bet", Bet.user_id == user.id, session) if bet.match.date_closed is None]

def get_user_hidden_bets(user, session=None):
  return get_condition_db("Bet", Bet.user_id == user.id & Bet.hidden == True, Bet.winner == 0, session)

def get_user_unhidden_bets(user, session=None):
  return get_condition_db("Bet", Bet.user_id == user.id & Bet.hidden == False, session)

def get_user_visible_current_bets(user, session=None):
  return get_condition_db("Bet", Bet.winner == 0 & ((Bet.user_id == user.id) | (Bet.user_id != user.id & Bet.hidden == False)), session)

def get_user_visible_bets(user, session=None):
  return get_condition_db("Bet", Bet.user_id == user.id | (Bet.user_id != user.id & Bet.hidden == False), session)

def bets_to_name_objs(bets, session=None):
  return add_time_name_objs([(shorten_bet_name(bet, session), bet) for bet in bets])

def matches_to_name_objs(matches, session=None):
  return add_time_name_objs([(shorten_match_name(match), match) for match in matches])

def bets_to_names(bets, session=None):
  return [no[0] for no in add_time_name_objs([(shorten_bet_name(bet, session), bet) for bet in bets])]

def matches_to_names(matches, session=None):
  return [no[0] for no in add_time_name_objs([(shorten_match_name(match), match) for match in matches])]