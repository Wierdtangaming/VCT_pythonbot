from dbinterface import get_from_db, is_key_in_db, add_to_db, delete_from_db
from sqlaobjs import Session
from Color import Color
from utils import hex_to_tuple, get_xkcd_color, get_random_hex_color

import secrets


def valid_hex(hex):
  if hex is None:
    return None
  if len(hex) != 6 and len(hex) != 7:
    return None

  if len(hex) == 7 and hex[0] != "#":
    return None
  else:
    
    hex = hex[-6:].lower()
  try:
    int(hex, 16)
    return hex
  except ValueError:
    return None
  
  
def get_color(name, session=None):
  name = name
  color = get_from_db("Color", name, session)
  return color
  
  
def add_color(name, hex, session=None):
  if session is None:
    with Session.begin() as session:
      return add_color(name, hex, session)
  name = name.capitalize()
  hex = hex.lower()
  if is_key_in_db("Color", name, session):
    return (f"{name} is already a color.", None)

  old_hex = hex
  if (hex := valid_hex(hex)) is None:
    return (f"{old_hex} is not a valid hex code. Only include the 6 numbers/letters.", None)

  color = Color(name, hex)
  add_to_db(color, session)
  return (f"{name} has been added to the color list.", color)
  
  
async def remove_color(name, session=None):
  if session is None:
    with Session.begin() as session:
      return await remove_color(name, session)
    
  name = name.capitalize()
  if not is_key_in_db("Color", name, session):
    return (f"{name} was not found in color list.", False)
  
  await delete_from_db(name, table_name="Color", session=session)     
  return (f"Removed {name} from color list", True)


def rename_color(old_name, new_name, session=None):
  if session is None:
    with Session.begin() as session:
      return rename_color(old_name, new_name, session)
      
  old_name = old_name.capitalize()
  new_name = new_name.capitalize()
  
  color = get_from_db("Color", old_name, session)
  if color is None:
    return (f"{old_name} was not found in color list.", None)
  teams = color.teams
  tournaments = color.tournaments
  users = color.users
  
  color.name = new_name
  for team in teams:
    team.set_color(color, session)
  for tournament in tournaments:
    tournament.set_color(color, session)
  for user in users:
    user.set_color(color, session)
  return (f"{old_name} has been renamed to {new_name}", color)
    
  
def recolor_color(name, hex, session=None):
  if session is None:
    with Session.begin() as session:
      return recolor_color(name, hex, session)
    
  name = name.capitalize()
  old_hex = hex
  if (hex := valid_hex(hex)) is None:
    return (f"{old_hex} is not a valid hex code. Only include the 6 numbers/letters.", None)
  
  color = get_from_db("Color", name, session)
  if color is None:
    return (f"{name} was not found in color list.", None)
  
  color.hex = hex
  for team in color.teams:
    team.set_color(color, session)
  for tournament in color.tournaments:
    tournament.set_color(color, session)
  for user in color.users:
    user.set_color(color, session)
  return (f"{name} now has the hex {hex}", color)

async def get_color_from_options(ctx, color=None, xkcd_color_name=None, color_name=None, session=None):
  if session is None:
    with Session.begin() as session:
      return await get_color_from_options(ctx, color, xkcd_color_name, color_name, session)

  count = 0
  if xkcd_color_name is not None:
    count += 1
  if color_name is not None:
    count += 1
  if color is not None:
    count += 1
  if count == 0:
    return get_random_hex_color()
  
  if count != 1:
    await ctx.respond("Please only enter one color.", ephemeral = True)
    return None
  
  if color is not None:
    color = valid_hex(color)
    if color is None:
      await ctx.respond("Invalid hex color.", ephemeral=True)
      return None
  elif xkcd_color_name is not None:
    color = get_xkcd_color(xkcd_color_name)
    if color is None:
      await ctx.respond("Invalid xkcd color.", ephemeral=True)
      return None
  elif color_name is not None:
    color_name = color_name.capitalize()
    color = get_from_db("Color", color_name, session)
    if color is None:
      await ctx.respond("Invalid color name.", ephemeral=True)
      return None
  return color

async def get_hex_from_options(ctx, hex=None, xkcd_color_name=None, color_name=None, session=None):
  if session is None:
    with Session.begin() as session:
      return await get_hex_from_options(ctx, hex, xkcd_color_name, color_name, session)

  color = await get_color_from_options(ctx, hex, xkcd_color_name, color_name, session)
  if color is None:
    return None
  if isinstance(color, Color):
    return color.hex
  else:
    return color
