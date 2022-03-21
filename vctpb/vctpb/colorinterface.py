
from savefiles import get_file, save_file

#color start
def valid_hex(hex):
  if len(hex) != 6 and len(hex) != 7:
    return None

  if len(hex) == 7 and hex[0] != "#":
    return None
  else:
    
    hex = hex[-6:]
  try:
    int(hex, 16)
    return hex
  except ValueError:
    return None

def get_all_colors():
  colors = dict(get_file("colors"))
  return colors

def get_all_colors_key_hex():
  colors = dict(get_file("colors"))
  return list(colors.items())

def save_colors(colors):
  save_file("colors", colors)

def hex_to_tuple(hex):
  if len(hex) != 6:
    return None
    
  return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
  
def get_color(name):
  name = name.lower()
  colors = get_all_colors()
  return colors.get(name)
  
def add_color(name, hex):
  name = name.lower()
  cap_name = name.capitalize()
  hex = hex.lower()
  colors = get_all_colors()
  if (old_color := colors.get(name)) is not None:
    return f"{cap_name} is already a color {old_color}."

  old_hex = hex
  if (hex := valid_hex(hex)) is None:
    return f"{old_hex} is not a valid hex code. Only include the 6 numbers/letters."

  colors[name] = hex
  save_colors(colors)
  return f"{cap_name} has been added to the color list."
  
def remove_color(name):
  name = name.lower()
  colors = get_all_colors()
  cap_name = name.capitalize()
  if (color := colors.pop(name, None)) is None:
    return (f"{cap_name} was not found in color list.", color)
  save_colors(colors)
  return (f"Removed {cap_name} from color list", color)

def rename_color(old_name, new_name):
  if (old_hex := remove_color(old_name)[1]) is None:
    return f"Could not find {old_name}."
  add_color(new_name, old_hex)
  return f"{old_name.capitalize()} is now {new_name.capitalize()}"
  
def recolor_color(name, hex):
  name = name.lower()
  cap_name = name.capitalize()
  hex = hex.lower()
  colors = get_all_colors()
  if colors.get(name) is None:
    return f"{cap_name} is not a color."
  old_hex = hex
  if (hex := valid_hex(hex)) is None:
    return f"{old_hex} is not a valid hex code. Only include the 6 numbers/letters."

  colors[name] = hex
  save_colors(colors)
  return f"{cap_name} now has the color {hex}"