from hashlib import new
from dbinterface import get_all_db, get_from_db, is_key_in_db, add_to_db, delete_from_db
from sqlaobjs import Session
from Color import Color

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
  
def get_color(name):
  name = name.lower()
  color = get_from_db("Color", name)
  return color
  
def add_color(name, hex):
  name = name.capitalize()
  hex = hex.lower()
  if is_key_in_db("Color", name):
    return f"{name} is already a color."

  old_hex = hex
  if (hex := valid_hex(hex)) is None:
    return f"{old_hex} is not a valid hex code. Only include the 6 numbers/letters."

  color = Color(name, hex)
  add_to_db("Color", color)
  return f"{name} has been added to the color list."
  
def remove_color(name):
  name = name.capitalize()
  with Session.begin() as session:
    if not is_key_in_db("Color", name, session):
      return f"{name} was not found in color list."
    delete_from_db("Color", name, session)
  return f"Removed {name} from color list"

def rename_color(old_name, new_name):
  old_name = old_name.capitalize()
  new_name = new_name.capitalize()
  with Session.begin() as session:
    color = get_from_db("Color", old_name, session)
    if color is None:
      return f"{old_name} was not found in color list."
    color.name = new_name
  return f"{old_name} has been renamed to {new_name}"
    
  
def recolor_color(name, hex):
  name = name.capitalize()
  if (hex := valid_hex(hex)) is None:
    return f"{hex} is not a valid hex code. Only include the 6 numbers/letters."
  with Session.begin() as session:
    color = get_from_db("Color", name, session)
    if color is None:
      return f"{hex} was not found in color list."
    color.hex = hex
  return f"{name} now has the color {hex}"