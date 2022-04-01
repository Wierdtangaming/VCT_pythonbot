from olddbinterface import get_from_list
import math
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqltypes import JSONLIST
from datetime import datetime

from sqlaobjs import mapper_registry

@mapper_registry.mapped
class Bet():
  
  __tablename__ = "bet"
  
  code = Column(String(8), primary_key = True, nullable=False)
  t1 = Column(String(50), nullable=False)
  t2 = Column(String(50), nullable=False)
  tournament_name = Column(String(100), nullable=False)
  winner = Column(Integer, nullable=False)
  amount_bet = Column(Integer, nullable=False)
  team_num = Column(Integer, nullable=False)
  color = Column(String(6), nullable=False)
  match_id = Column(String(8), ForeignKey("match.code"), nullable=False)
  match = relationship("Match", back_populates="bets")
  user_id = Column(Integer, ForeignKey("user.code"), nullable=False)
  user = relationship("User", back_populates="bets")
  date_created = Column(DateTime, nullable=False)
  message_ids = Column(JSONLIST, nullable=False)
  
  
  def __init__(self, code, t1, t2, tournament_name, amount_bet, team_num, color, match_id, user_id, date_created):
    
    self.code = code
    
    self.t1 = t1
    self.t2 = t2
    self.tournament_name = tournament_name
    
    self.winner = 0
    
    self.amount_bet = amount_bet
    self.team_num = team_num
    
    self.color = color
    
    self.match_id = match_id
    self.user_id = user_id
    self.date_created = date_created

    #team num of winner
    self.message_ids = []

  def __init__(self, code, t1, t2, tournament_name, winner, amount_bet, team_num, color, match_id, user_id, date_created, message_ids):
      self.code = code
      self.t1 = t1
      self.t2 = t2
      self.tournament_name = tournament_name
      self.winner = winner
      self.amount_bet = amount_bet
      self.team_num = team_num
      self.color = color
      self.match_id = match_id
      self.user_id = user_id
      self.date_created = date_created
      self.message_ids = message_ids
  
  def __repr__(self):
    return f"<Bet {self.code}>"

  def to_string(self):
    date_formatted = self.date_created.strftime("%d/%m/%Y at %H:%M:%S")
    return "Match ID: " + str(self.match_id) + ", User ID: " + str(self.user_id) + ", Amount Bet: " + str(self.amount_bet) + ", Team Bet On: " + str(self.team_num) + ", Date Created: " + str(date_formatted) + ", Date Closed: " + str(self.date_closed) + ", Winner: " + str(self.winner) + ", Identifyer: " + str(self.code) + ", Message IDs: " + str(self.message_ids)

  
  
  def get_team(self):
    if self.team_num == 1:
      return self.t1
    elif self.team_num == 2:
      return self.t2
    
  def get_match(self):
    return get_from_list("match", self.match_id)
    
  def get_team_and_payout(self):
    match = get_from_list("match", self.match_id)

    team = ""
    payout = 0.0
    print()
    if self.team_num == 1:
      team = match.t1
      payout = self.amount_bet * match.t1o - self.amount_bet
    elif self.team_num == 2:
      team = match.t2
      payout = self.amount_bet * match.t2o - self.amount_bet

    return(team, payout)

  def get_team_and_winner(self):

    team = ""
    winner = ""

    if self.team_num == 1:
      team = self.t1
    elif self.team_num == 2:
      team = self.t2

    if self.winner == 1:
      winner = self.t1
    elif self.winner == 2:
      winner = self.t2
    elif self.winner == 0:
      winner = "None"

    return(team, winner)

  async def short_to_string(self, bot):
    
    (team, payout) = self.get_team_and_payout()

    return f"User: <@!{self.user_id}>, Team: {team}, Amount: {self.amount_bet}, Payout: {int(math.floor(payout))}"

  async def basic_to_string(self, bot, match=None):
    if match is None:
      match = get_from_list("match", self.match_id)

    return f"Bet: {self.code}, User: <@!{self.user_id}>, Team: {self.get_team()}, Amount: {self.amount_bet}, Match ID: {match.code}"
  
  def balance_to_string(self, balance):
    
    match = get_from_list("match", self.match_id)
    (team, winner) = self.get_team_and_winner()

    return f"{match.t1} vs {match.t2}, Bet on: {team}, Winner: {winner}, Amount bet: {math.floor(self.amount_bet)}, Balance change: {math.floor(balance)}"

def is_valid_bet(code, t1, t2, tournament_name, winner, amount_bet, team_num, color, match_id, user_id, date_created, message_ids):
  errors = [False for _ in range(12)]
  if isinstance(code, str) == False or len(code) != 8:
    errors[0] = True
  if isinstance(t1, str) == False or len(t1) > 50:
    errors[1] = True
  if isinstance(t2, str) == False or len(t2) > 50:
    errors[2] = True
  if isinstance(tournament_name, str) == False or len(tournament_name) > 100:
    errors[3] = True
  if isinstance(winner, int) == False:
    errors[4] = True
  if isinstance(amount_bet, int) == False:
    errors[5] = True
  if isinstance(team_num, int) == False:
    errors[6] = True
  if isinstance(color, str) == False or len(color) != 6:
    errors[7] = True
  if isinstance(match_id, str) == False or len(match_id) != 8:
    errors[8] = True
  if isinstance(user_id, int) == False:
    errors[9] = True
  if isinstance(date_created, datetime) == False:
    errors[10] = True
  if isinstance(message_ids, list) == False:
    errors[11] = True
  return errors
