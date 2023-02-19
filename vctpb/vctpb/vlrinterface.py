# web scape the VLR.gg main page

#import libraries
import re
from bs4 import BeautifulSoup
from urllib.request import urlopen

from sqlaobjs import Session
from convert import get_active_tournaments

from Tournament import Tournament
from Team import Team
from Match import Match
from objembed import create_match_embedded, channel_send_match_list_embedded
from dbinterface import get_channel_from_db, get_from_db, add_to_db, get_unique_code
from autocompletes import get_team_from_vlr_code, get_match_from_vlr_code, get_tournament_from_vlr_code
from utils import get_random_hex_color, balance_odds, mix_colors, get_date, to_float, to_digit


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

def get_or_create_team(team_name, team_vlr_code, session=None):
  if session is None:
    with Session.begin() as session:
      get_or_create_team(team_name, team_vlr_code, session)
  team = get_from_db("Team", team_name, session)
  if team is not None:
    if team.vlr_code is None:
      print(f"team {team_name} has no vlr code, setting to {team_vlr_code}")
      team.vlr_code = team_vlr_code
    return team
  if team_vlr_code is not None:
    team = get_team_from_vlr_code(team_vlr_code, session)
    if team is not None:
      return team
  team = Team(team_name, team_vlr_code, get_random_hex_color())
  add_to_db(team, session)
  return team

def vlr_create_match(match_code, tournament, session=None):
  if session is None:
    with Session.begin() as session:
      vlr_create_match(match_code, tournament, session)
      
  if get_match_from_vlr_code(match_code, session) is not None:
    return None
      
  match_link = get_match_link(match_code)
  html = urlopen(match_link)
  soup = BeautifulSoup(html, 'html.parser')
  t1_link_div = soup.find("a", class_="match-header-link wf-link-hover mod-1")
  t2_link_div = soup.find("a", class_="match-header-link wf-link-hover mod-2")
  if t1_link_div is None or t2_link_div is None:
    print(f"team link not found for match https://www.vlr.gg/{match_code}")
    return None
  
  t1_vlr_code = t1_link_div.get("href").split("/")[2]
  t2_vlr_code = t2_link_div.get("href").split("/")[2]
  
  t1_vlr_odds_label = soup.find("span", class_="match-bet-item-odds mod- mod-1")
  t2_vlr_odds_label = soup.find("span", class_="match-bet-item-odds mod- mod-2")
  
  if t1_vlr_odds_label is None or t2_vlr_odds_label is None:
    print(f"odds not found for https://www.vlr.gg/{match_code}")
    return None
  
  t1oo = to_float(t1_vlr_odds_label.get_text().strip())
  t2oo = to_float(t2_vlr_odds_label.get_text().strip())
  
  if t1oo is None or t2oo is None:
    print(f"odds not found for match https://www.vlr.gg/{match_code}")
    return None
  if t1oo <= 1 or t2oo <= 1:
    print(f"odds not found for match https://www.vlr.gg/{match_code}")
    return None
  
  t1o, t2o = balance_odds(t1oo, t2oo)
  
  names = soup.find_all("span", class_="match-bet-item-team")
  if len(names) != 2:
    names = soup.find_all("div", class_="wf-title-med")
    if len(names) != 2:
      names = soup.find_all("div", class_="wf-title-med ")
      if len(names) != 2:
        names = soup.find_all("div", class_="wf-title-med mod-single")
        if len(names) != 2:
          print(f"team names not found for match https://www.vlr.gg/{match_code}, names: {names}")
          return None
  
  t1_name = names[0].get_text().strip()
  t2_name = names[1].get_text().strip()
  
  team1 = get_or_create_team(t1_name, t1_vlr_code, session)
  team2 = get_or_create_team(t2_name, t2_vlr_code, session)
  
  t1 = team1.name
  t2 = team2.name
  
  odds_source = "VLR.gg"
  color_hex = mix_colors([team1.color_hex, team2.color_hex, tournament.color_hex])
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