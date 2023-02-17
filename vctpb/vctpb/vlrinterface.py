# web scape the VLR.gg main page

#import libraries
import re
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.request import urlopen

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

# returs the matches for the day and a boolean indicating if tournament is over
def vlr_get_today_matches(tournament_code):
  tournament_link = get_tournament_link(tournament_code)
  html = urlopen(tournament_link)
  soup = BeautifulSoup(html, 'html.parser')
  
  date_labels = soup.find_all("div", class_="wf-label mod-large")
  
  # top is not a matches card
  day_matches_cards = soup.find_all("div", class_="wf-card")
  day_matches_cards.pop(0)
  
  index = 0;
  for date_label in date_labels:
    date = date_label.get_text()
    if date.__contains__("Today"):
      break;
    index += 1
  
  # no games today
  if index == len(date_labels):
    return [], True
  
  match_cards = day_matches_cards[index].find_all("a", class_="wf-module-item")
  match_codes = []
  for match_card in match_cards:
    match_code = match_card.get("href")
    if match_code is not None:
      match_codes.append((int)(match_code.split("/")[1]))
  return match_codes, True


def vlr_get_match_info(match_code):
  match_link = get_match_link(match_code)
  html = urlopen(match_link)
  soup = BeautifulSoup(html, 'html.parser')
  
  t1_vlr_code = soup.find("a", class_="match-header-link wf-link-hover mod-1").get("href").split("/")[2]
  t2_vlr_code = soup.find("a", class_="match-header-link wf-link-hover mod-2").get("href").split("/")[2]
  
  t1_vlr_odds = soup.find("span", class_="match-bet-item-odds mod- mod-1").get_text()
  t2_vlr_odds = soup.find("span", class_="match-bet-item-odds mod- mod-2").get_text()
  
  return t1_vlr_code, t2_vlr_code, t1_vlr_odds, t2_vlr_odds
