import math
from decimal import Decimal
import secrets
from datetime import datetime
from pytz import timezone
import colorsys
import mixbox

import matplotlib.colors as mcolors

xkcd_colors = mcolors.XKCD_COLORS

def get_xkcd_color(name):
  return xkcd_colors.get(f"xkcd:{name.lower()}")[-6:]

def get_date():
  central = timezone('US/Central')
  return datetime.now(central)

def get_date_string(date=None):
  if date is None:
    date = get_date()
  return date.strftime("%Y-%m-%d-%H-%M-%S")

def roundup(x):
  return math.ceil(Decimal(x) * Decimal(1000)) / Decimal(1000)

def balance_odds(team_one_old_odds, team_two_old_odds):
  odds1 = team_one_old_odds - 1
  odds2 = team_two_old_odds - 1
  
  oneflip = 1 / odds1
  
  percentage1 = (math.sqrt(odds2/oneflip))
  
  team_one_odds = roundup(odds1 / percentage1) + 1
  team_two_odds = roundup(odds2 / percentage1) + 1
  return team_one_odds, team_two_odds

def mix_colors(colors):
  rgb_tuples = [(hex_to_tuple(hex), weight) for hex, weight in colors]
  total_weight = sum(weight for _, weight in rgb_tuples)
  latent_tuples = [(mixbox.rgb_to_latent(rgb), weight / total_weight) for rgb, weight in rgb_tuples]
  
  latent_mix = [0] * mixbox.LATENT_SIZE
  for i in range(len(latent_mix)):
    latent_mix[i] = sum(weight * latent[i] for latent, weight in latent_tuples)
  
  return tuple_to_hex(mixbox.latent_to_rgb(latent_mix))

def get_random_hex_color():
  return str(secrets.token_hex(3))

def hex_to_tuple(hex):
  if len(hex) != 6:
    return None
    
  return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

def tuple_to_hex(tup):
  if len(tup) != 3:
    return None
    
  return f"{tup[0]:02x}{tup[1]:02x}{tup[2]:02x}"
  

def is_digit(str):
  try:
    int(str)
    return True
  except ValueError:
    return False
  
def to_digit(str):
  try:
    i = int(str)
    return i
  except ValueError:
    return None
  
def is_float(str):
  try:
    float(str)
    return True
  except ValueError:
    return None

def to_float(str):
  try:
    f = float(str)
    return f
  except ValueError:
    return None