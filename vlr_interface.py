# web scape the VLR.gg main page

#import libraries
import re
from PIL import Image
from collections import Counter
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.request import urlopen

#entered_tournament_link = "https://www.vlr.gg/event/1188/champions-tour-2023-lock-in-s-o-paulo"

#entered_match_link = "https://www.vlr.gg/167356/nrg-esports-vs-giants-gaming-champions-tour-2023-lock-in-s-o-paulo-alpha-qf"

entered_team_link = "https://www.vlr.gg/team/1034/nrg-esports"
entered_team_link = "https://www.vlr.gg/team/6961/loud/"

def to_digit(str):
  try:
    i = int(str)
    return i
  except ValueError:
    return None
  
def get_code(link):
  split_link = link.split("/")
  if len(split_link) == 0:
    return None
  if len(split_link) >= 2:
    if (code := to_digit(split_link[-2])) is not None:
      return code
  for part in split_link:
    if (code := to_digit(part)) is not None:
      return code

def get_tournament_link(code):
  link = "https://www.vlr.gg/event/matches/" + str(code) + "/?group=upcoming&series_id=all"
  return link

def get_match_link(code):
  link = "https://www.vlr.gg/" + str(code)
  return link

def get_team_link(code):
  link = "https://www.vlr.gg/team/" + str(code)
  return link

def load_img(img_link):
  response = requests.get(img_link, stream=True)
  img = Image.open(response.raw)
  return img.convert("RGBA")

def get_color_count(img):
  pixels = [p[:3] for p in img.getdata() if p[3] < 255]
  counts = Counter(pixels)
  return counts
  

#finds the most common pixel in the image image is a link to the image
#clears colorless pixels
def get_most_common_color(img_link):
  
  threshold = 0.8
  
  img = load_img(img_link)
  
  # Get a list of all the non-transparent pixel values in the image
  pixels = [p[:3] for p in img.getdata() if p[3] != 0]
      
  # Get the total number of pixels in the image
  total_pixels = len(pixels)

  # Get the number of "colorless" pixels (i.e. pixels where the RGB values are all within 50 of each other)
  colorless_pixels = [p for p in pixels if max(p) - min(p) <= 50]
  colorless_count = len(colorless_pixels)

  # Remove the "colorless" pixels if their total count is less than 90% of the total number of pixels
  if colorless_count / total_pixels < threshold:
      pixels = [p for p in pixels if max(p) - min(p) > 50]

  # Recount the frequency of each pixel value
  counts = Counter(pixels)

  # Get the most common pixel value (which will be a tuple of RGB values)
  most_common = counts.most_common(1)[0][0]

  return most_common
  
  
def get_img_link(soup, team_name):
  img = soup.find("img", alt=f"{team_name} team logo")
  if img is None:
    return None
  return "http:" + img.get("src")

def get_color_from_vlr_page(soup, team_name):
  img_link = get_img_link(soup, team_name)
  color = get_most_common_color(img_link)

team_code = get_code(entered_team_link)
team_link = get_team_link(team_code)
print(team_link)
html = urlopen(team_link)
soup = BeautifulSoup(html, 'html.parser')

name = soup.find("h1", class_="wf-title").get_text()
get_color_from_vlr_page(soup, name)