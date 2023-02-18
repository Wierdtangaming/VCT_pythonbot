# web scape the VLR.gg main page

#import libraries
import re
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.request import urlopen

entered_tournament_link = "https://www.vlr.gg/event/1188/champions-tour-2023-lock-in-s-o-paulo"

#entered_match_link = "https://www.vlr.gg/167356/nrg-esports-vs-giants-gaming-champions-tour-2023-lock-in-s-o-paulo-alpha-qf"

#entered_team_link = "https://www.vlr.gg/team/1034/nrg-esports"

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

def vlr_get_today_matches(tournament_code) -> list:
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
    return []
  
  match_cards = day_matches_cards[index].find_all("a", class_="wf-module-item")
  match_codes = []
  for match_card in match_cards:
    match_code = match_card.get("href")
    if match_code is not None:
      match_codes.append((int)(match_code.split("/")[1]))
  return match_codes


def vlr_get_match_info(match_code):
  match_link = get_match_link(match_code)
  html = urlopen(match_link)
  soup = BeautifulSoup(html, 'html.parser')
  t1_link_div = soup.find("a", class_="match-header-link wf-link-hover mod-1")
  t2_link_div = soup.find("a", class_="match-header-link wf-link-hover mod-2")
  if t1_link_div is None or t2_link_div is None:
    print("team link not found for match code {match_code}")
    return None, None, None, None
  t1_vlr_code = t1_link_div.get("href").split("/")[2]
  t2_vlr_code = t2_link_div.get("href").split("/")[2]
  
  t1_vlr_odds_label = soup.find("span", class_="match-bet-item-odds mod- mod-1")
  t2_vlr_odds_label = soup.find("span", class_="match-bet-item-odds mod- mod-2")
  if t1_vlr_odds_label is None or t2_vlr_odds_label is None:
    print("odds not found for match code {match_code}")
    return None, None, None, None
  t1_vlr_odds = t1_vlr_odds_label.get_text()
  t2_vlr_odds = t2_vlr_odds_label.get_text()
  
  return t1_vlr_code, t2_vlr_code, t1_vlr_odds, t2_vlr_odds
  


#get codes
tournament_code = get_code(entered_tournament_link)

match_codes = vlr_get_today_matches(tournament_code)

print(match_codes)

for match_code in match_codes:
    print(vlr_get_match_info(match_code))
