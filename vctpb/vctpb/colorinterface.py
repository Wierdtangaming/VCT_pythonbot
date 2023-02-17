from dbinterface import get_from_db, is_key_in_db, add_to_db, delete_from_db
from sqlaobjs import Session
from Color import Color


# hex is a string
def mix_colors(hex1, hex2):
  r1, g1, b1 = hex_to_tuple(hex1)
  r2, g2, b2 = hex_to_tuple(hex2)
  r = (r1 + r2) // 2
  g = (g1 + g2) // 2
  b = (b1 + b2) // 2
  return f"#{r:02x}{g:02x}{b:02x}"
  

def valid_hex(hex):
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


def hex_to_tuple(hex):
  if len(hex) != 6:
    return None
    
  return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
  
  
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
    team.set_color(color)
  for tournament in tournaments:
    tournament.set_color(color)
  for user in users:
    user.set_color(color)
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
    team.set_color(color)
  for tournament in color.tournaments:
    tournament.set_color(color)
  for user in color.users:
    user.set_color(color)
  return (f"{name} now has the hex {hex}", color)