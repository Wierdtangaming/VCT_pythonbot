# web scape the VLR.gg main page

#import libraries
import re
from bs4 import BeautifulSoup
from urllib.request import urlopen
from PIL import Image
from collections import Counter
import requests

from sqlaobjs import Session
from convert import get_active_tournaments

from Tournament import Tournament
from Team import Team
from Match import Match
from objembed import create_match_embedded, channel_send_match_list_embedded
from dbinterface import get_channel_from_db, get_from_db, add_to_db, get_unique_code
from autocompletes import get_team_from_vlr_code, get_match_from_vlr_code, get_tournament_from_vlr_code
from utils import get_random_hex_color, balance_odds, mix_colors, get_date, to_float, to_digit, tuple_to_hex


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
  
  threshold = 0.85
  
  img = load_img(img_link)
  
  # Get a list of all the non-transparent pixel values in the image
  pixels = [p[:3] for p in img.getdata() if p[3] != 0]
      
  # Get the total number of pixels in the image
  total_pixels = len(pixels)

  # Get the number of "colored" pixels (i.e. pixels where the RGB values are all not within 30 of each other)
  colored_pixels = [p for p in pixels if max(p) - min(p) > 30]
  colored_count = len(colored_pixels)

  
  if colored_count / total_pixels > 1 - threshold:
      pixels = colored_pixels

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
  return tuple_to_hex(color)

def update_team_with_vlr_code(team, team_vlr_code, soup = None, session = None):
  if team.vlr_code is None:
    if team_vlr_code is None:
      return
    team.vlr_code = team_vlr_code
    if soup is None:
      html = urlopen(get_team_link(team_vlr_code))
      soup = BeautifulSoup(html, 'html.parser')
    team.set_color(get_color_from_vlr_page(soup, team.name), session)

def vlr_get_today_matches(tournament_code) -> list:
  tournament_link = get_tournament_link(tournament_code)
  html = urlopen(tournament_link)
  soup = BeautifulSoup(html, 'html.parser')
  
  date_labels = soup.find_all("div", class_="wf-label mod-large")
  
  # top is not a matches card
  day_matches_cards = soup.find_all("div", class_="wf-card")
  day_matches_cards.pop(0)
  
  if len(day_matches_cards) == 0:
    return []
  
  index = 0;
  for date_label in date_labels:
    date = date_label.get_text()
    if date.__contains__("Today"):
      break;
    index += 1
  
  index = 2;
  
  # no games today
  if index == len(date_labels):
    return []
  
  match_cards = day_matches_cards[index].find_all("a", class_="wf-module-item")
  match_codes = []
  for match_card in match_cards:
    match_code = match_card.get("href")
    if match_code is not None:
      match_codes.append((int)(match_code.split("/")[1]))
  return match_codes

def get_or_create_team(team_name, team_vlr_code, session=None, soup=None):
  if session is None:
    with Session.begin() as session:
      get_or_create_team(team_name, team_vlr_code, soup, session)
      
  team = get_from_db("Team", team_name, session)
  if team is not None:
    update_team_with_vlr_code(team, team_vlr_code, soup, session)
    return team
  
  if team_vlr_code is not None:
    team = get_team_from_vlr_code(team_vlr_code, session)
    if team is not None:
      team.name = team_name
      return team
    if soup is None:
      html = urlopen(get_team_link(team_vlr_code))
      soup = BeautifulSoup(html, 'html.parser')
    color = get_color_from_vlr_page(soup, team_name)
  else:
    color = get_random_hex_color()
    
  team = Team(team_name, team_vlr_code, color)
  add_to_db(team, session)
  return team


def get_team_codes_from_match_page(soup):
  t1_link_div = soup.find("a", class_="match-header-link wf-link-hover mod-1")
  t2_link_div = soup.find("a", class_="match-header-link wf-link-hover mod-2")
  if t1_link_div is None or t2_link_div is None:
    print(f"team link not found")
    return None, None
  
  t1_vlr_code = t1_link_div.get("href").split("/")[2]
  t2_vlr_code = t2_link_div.get("href").split("/")[2]
  return t1_vlr_code, t2_vlr_code

def get_odds_from_match_page(soup):
  t1_vlr_odds_label = soup.find("span", class_="match-bet-item-odds mod- mod-1")
  t2_vlr_odds_label = soup.find("span", class_="match-bet-item-odds mod- mod-2")
  
  if t1_vlr_odds_label is None or t2_vlr_odds_label is None:
    print(f"1 odds not found")
    return None, None
  
  t1oo = to_float(t1_vlr_odds_label.get_text().strip())
  t2oo = to_float(t2_vlr_odds_label.get_text().strip())
  
  if t1oo is None or t2oo is None:
    print(f"2 odds not found")
    return None, None
  if t1oo <= 1 or t2oo <= 1:
    print(f"3 odds not found")
    return None, None
  
  return t1oo, t2oo

def get_team_names_from_match_page(soup):
  names = soup.find_all("span", class_="match-bet-item-team")
  if len(names) != 2:
    names = soup.find_all("div", class_="wf-title-med")
    if len(names) != 2:
      names = soup.find_all("div", class_="wf-title-med ")
      if len(names) != 2:
        names = soup.find_all("div", class_="wf-title-med mod-single")
        if len(names) != 2:
          print(f"team names not found, names: {names}")
          return None, None
  
  t1_name = names[0].get_text().strip()
  t2_name = names[1].get_text().strip()
  
  return t1_name, t2_name

def get_teams_from_match_page(soup, session):
  t1_vlr_code, t2_vlr_code = get_team_codes_from_match_page(soup)
  t1_name, t2_name = get_team_names_from_match_page(soup)
  if t1_vlr_code is None or t1_name is None:
    return None, None
  
  team1 = get_or_create_team(t1_name, t1_vlr_code, session, soup)
  team2 = get_or_create_team(t2_name, t2_vlr_code, session, soup)
  return team1, team2
  
def vlr_create_match(match_code, tournament, session=None):
  if session is None:
    with Session.begin() as session:
      vlr_create_match(match_code, tournament, session)
  
  if get_match_from_vlr_code(match_code, session) is not None:
    print("match already exists")
    return None
      
  match_link = get_match_link(match_code)
  html = urlopen(match_link)
  soup = BeautifulSoup(html, 'html.parser')
  
  t1oo, t2oo = get_odds_from_match_page(soup)
  if t1oo is None:
    return None
  t1o, t2o = balance_odds(t1oo, t2oo)
  
  team1, team2 = get_teams_from_match_page(soup, session)
  if team1 is None:
    return None
  
  t1 = team1.name
  t2 = team2.name
  
  odds_source = "VLR.gg"
  color_hex = mix_colors([(team1.color_hex, 3), (team2.color_hex, 3), (tournament.color_hex, 1)])
  date_created = get_date()
  code = get_unique_code("Match", session)
    
  return Match(code, t1, t2, t1o, t2o, t1oo, t2oo, tournament.name, odds_source, color_hex, None, date_created, match_code)


async def generate_matches(bot, session=None):
  if session is None:
    with Session.begin() as session:
      generate_matches(bot, session)
  
  tournaments = get_active_tournaments(session)
  
  matches = []
  
  match_channel = await bot.fetch_channel(get_channel_from_db("match", session))
  
  for tournament in tournaments:
    match_codes = vlr_get_today_matches(tournament.vlr_code)
    print(f"generating matches with codes: {match_codes}")
    for match_code in match_codes:
      match = vlr_create_match(match_code, tournament, session)
      if match is None:
        continue
      add_to_db(match, session)
      
      embedd = create_match_embedded(match, f"New Match: {match.t1} vs {match.t2}, {match.t1o} / {match.t2o}.", session)
      
      if match_channel is not None:
        msg = await match_channel.send(embed=embedd)
        match.message_ids.append((msg.id, msg.channel.id))
      matches.append(match)
  
  if match_channel is not None:
    if len(matches) != 1:
      await channel_send_match_list_embedded(match_channel, "Generated Matches:", matches, session)

def get_or_create_tournament(tournament_name, tournament_vlr_code, session=None):
  if session is None:
    with Session.begin() as session:
      get_or_create_tournament(tournament_name, tournament_vlr_code, session)
      
  tournament = get_from_db("Tournament", tournament_name, session)
  if tournament is not None:
    if tournament.vlr_code is not None:
      return tournament
    tournament.vlr_code = tournament_vlr_code
    return tournament
  
  if tournament_vlr_code is not None:
    tournament = get_tournament_from_vlr_code(tournament_vlr_code, session)
    if tournament is not None:
      return tournament
  tournament = Tournament(tournament_name, tournament_vlr_code, get_random_hex_color())
  add_to_db(tournament, session)
  return tournament
  
def generate_tournament(vlr_code, color, session=None):
  if session is None:
    with Session.begin() as session:
      generate_tournament(vlr_code, session)
      
  if get_tournament_from_vlr_code(vlr_code, session) is not None:
    return None
  
  tournament_link = get_tournament_link(vlr_code)
  print(f"generating tournament from link: {tournament_link}")
  html = urlopen(tournament_link)
  soup = BeautifulSoup(html, 'html.parser')
  tournament_name = soup.find("h1", class_="wf-title").get_text().strip()
  tournament_color = color
  tournament = Tournament(tournament_name, vlr_code, tournament_color)
  add_to_db(tournament, session)
  return tournament