# web scape the VLR.gg main page

#import libraries
import re
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.request import urlopen

from sqlaobjs import Session
from convert import get_current_tournaments
from dbinterface import get_condition_db, get_from_db, add_to_db

from Tournament import Tournament

def get_code(link):
  code = link.split("/")[-2]
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

def get_or_create_team(team_name, team_code, session=None):
  if session is None:
    with Session.begin() as session:
      get_or_create_team(team_name, session)


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


def vlr_create_match(match_code):
  match_link = get_match_link(match_code)
  html = urlopen(match_link)
  soup = BeautifulSoup(html, 'html.parser')
  
  t1_vlr_code = soup.find("a", class_="match-header-link wf-link-hover mod-1").get("href").split("/")[2]
  t2_vlr_code = soup.find("a", class_="match-header-link wf-link-hover mod-2").get("href").split("/")[2]
  names = soup.find_all("div", class_="wf-title-med mod-single")
  t1_name = names[0].get_text()
  t2_name = names[1].get_text()
  
  team1 = get_or_create_team(t1_vlr_code)
  team2 = get_or_create_team(t2_vlr_code)
  t1_vlr_odds = soup.find("span", class_="match-bet-item-odds mod- mod-1").get_text()
  t2_vlr_odds = soup.find("span", class_="match-bet-item-odds mod- mod-2").get_text()
  
  dbGet
  return t1_vlr_code, t2_vlr_code, t1_vlr_odds, t2_vlr_odds


def generate_matches(session=None):
  if session is None:
    with Session.begin() as session:
      generate_matches(session)
  tournaments = get_current_tournaments(session)
  
  for tournament in tournaments:
    matches = vlr_get_today_matches(tournament.vlr_code)
    
    for match in matches: