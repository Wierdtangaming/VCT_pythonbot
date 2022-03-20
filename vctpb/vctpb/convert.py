
from Match import Match
from Bet import Bet
from User import User
import discord
from dbinterface import get_from_list, get_all_objects


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

def id_to_metion(id):
  return f"<@!{id}>"


  
async def get_user_from_member(ctx, user):
  if user == None:
    user = ctx.author
  user = get_from_list("user", user.id)
  if user == None:
    await ctx.respond("User not found. To create an account do $balance")
  return user


async def user_from_autocomplete_tuple(ctx, t_list, text, prefix):
  
  objs = [t[1] for t in t_list if text == t[0]]
  
  if len(objs) >= 2:
    print("More than one of text found", objs)
    if ctx is not None:
      await ctx.respond(f"Error please @pig. Try typing in code instead.")
    return None
  if len(objs) == 0:
    obj = get_from_list(prefix, text)
  else:
    obj = objs[0]
    
  if obj == [] or obj is None:
    if ctx is not None:
      await ctx.respond(f"{prefix.capitalize()} ID not found.")
    return None
  return obj


def get_user_from_username(username):
  users = get_all_objects("user")
  for user in users:
    if user.username == username:
      return user
  return None