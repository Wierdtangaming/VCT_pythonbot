import math
from decimal import Decimal
import secrets
from datetime import datetime
from pytz import timezone

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


# hexs are string
def mix_colors(hexs):
  r, g, b = 0, 0, 0
  for hex in hexs:
    r1, g1, b1 = hex_to_tuple(hex)
    r += r1
    g += g1
    b += b1
  r = r // len(hexs)
  g = g // len(hexs)
  b = b // len(hexs)
  return f"{r:02x}{g:02x}{b:02x}"

def get_random_hex_color():
  return str(secrets.token_hex(3))

def hex_to_tuple(hex):
  if len(hex) != 6:
    return None
    
  return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

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