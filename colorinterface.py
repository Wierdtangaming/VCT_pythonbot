
from replit import db

#color start
def valid_hex(hex):
  if len(hex) != 8:
    return False
  try:
    int(hex, 16)
    return True
  except ValueError:
    return False

def get_all_colors():
  colors = db["colors"]
  print(type(colors))
  return colors
  
def save_colors(colors):
  db["colors"] = colors

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
  hex = hex.lower()
  colors = get_all_colors()
  if old_color := colors.get(name) is not None:
    cap_name = name.capitalize()
    return f"{cap_name} is already a color {old_color}."
  if not valid_hex(hex):
    return f"{hex} is not a valid hex code."
    
  colors[name] = hex
  save_colors(colors)
  
def remove_color(name):
  name = name.lower()
  colors = get_all_colors()
  if color := color.pop(name, None) is not None:
    save_colors(colors)
  return color

def rename_color(old_name, new_name):
  if old_val := remove_color(ond_name) is None:
    return f"Could not find {old_name}."
  add_color(new_name)
  return f"{old_name.capitalize()} is now {new_name.capitalize()}"
  
def recolor_color(name, hex):
  name = name.lower()
  hex = hex.lower()
  colors = get_all_colors()
  if colors.get(name) is None:
    cap_name = name.capitalize()
    return f"{cap_name} is not a color."
  if not valid_hex(hex):
    return f"{hex} is not a valid hex code."
  colors[name] = hex
  save_colors(colors)