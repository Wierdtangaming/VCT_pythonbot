import math
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BOOLEAN
from sqlalchemy.orm import relationship
from sqltypes import JSONList, MsgMutableList
from sqlalchemy.ext.mutable import MutableList
from datetime import datetime
from sqlaobjs import mapper_registry, Session
from utils import mix_colors, get_random_hex_color


@mapper_registry.mapped
class Bet():
  
  __tablename__ = "bet"
  
  code = Column(String(8), primary_key = True, nullable=False)
  t1 = Column(String(50), ForeignKey("team.name"), nullable=False)
  team1 = relationship("Team", foreign_keys=[t1], back_populates="bets_as_t1")
  t2 = Column(String(50), ForeignKey("team.name"), nullable=False)
  team2 = relationship("Team", foreign_keys=[t2], back_populates="bets_as_t2")
  tournament_name = Column(String(100), ForeignKey("tournament.name"), nullable=False)
  tournament = relationship("Tournament", back_populates="bets")
  
  winner = Column(Integer, nullable=False)
  amount_bet = Column(Integer, nullable=False)
  team_num = Column(Integer, nullable=False)
  color_hex = Column(String(6), nullable=False)
  match_id = Column(String(8), ForeignKey("match.code"), nullable=False)
  match = relationship("Match", back_populates="bets")
  user_id = Column(Integer, ForeignKey("user.code"), nullable=False)
  user = relationship("User", back_populates="bets")
  date_created = Column(DateTime, nullable=False)
  message_ids = Column(MsgMutableList.as_mutable(JSONList), nullable=False)
  hidden = Column(BOOLEAN, nullable=False)
  
  
  def __init__(self, code, t1, t2, tournament_name, amount_bet, team_num, match_id, user_id, date_created, hidden):
    
    self.code = code
    
    self.t1 = t1
    self.t2 = t2
    self.tournament_name = tournament_name
    
    self.winner = 0
    
    self.amount_bet = amount_bet
    self.team_num = team_num
    
    self.match_id = match_id
    self.user_id = user_id
    self.date_created = date_created

    #team num of winner
    self.message_ids = []
    
    self.hidden = hidden
    self.set_color(from_init=True)

  def full__init__(self, code, t1, t2, tournament_name, winner, amount_bet, team_num, match_id, user_id, date_created, message_ids):
    self.code = code
    self.t1 = t1
    self.t2 = t2
    self.tournament_name = tournament_name
    self.winner = winner
    self.amount_bet = amount_bet
    self.team_num = team_num
    self.match_id = match_id
    self.user_id = user_id
    self.date_created = date_created
    self.message_ids = message_ids
    self.set_color(from_init=True)
  
  
  def __repr__(self):
    return f"<Bet {self.code}>"

  def set_color(self, session=None, from_init=False):
    if session is None:
      with Session.begin() as session:
        return self.set_color(session, from_init)
    
    from dbinterface import get_from_db  
    
    if from_init:
      team1 = get_from_db("Team", self.t1, session)
      team2 = get_from_db("Team", self.t2, session)
      user = get_from_db("User", self.user_id, session)
      match = get_from_db("Match", self.match_id, session)
    else:
      team1 = self.team1
      team2 = self.team2
      user = self.user
      match = self.match
      
    team_hex = team1.color_hex if self.team_num == 1 else team2.color_hex
    if self.hidden:
      hex = get_random_hex_color()
    else:
      hex = mix_colors([(team_hex, 3), (user.color_hex, 3), (match.color_hex, 1)])
    self.color_hex = hex
  
  
  def to_string(self):
    date_formatted = self.date_created.strftime("%d/%m/%Y at %H:%M:%S")
    return "Match ID: " + str(self.match_id) + ", User ID: " + str(self.user_id) + ", Amount Bet: " + str(self.amount_bet) + ", Team Bet On: " + str(self.team_num) + ", Date Created: " + str(date_formatted) + ", Winner: " + str(self.winner) + ", Identifyer: " + str(self.code) + ", Message IDs: " + str(self.message_ids)
    
    
  def get_team(self):
    if self.team_num == 1:
      return self.t1
    elif self.team_num == 2:
      return self.t2
    
  def get_payout(self):
    match = self.match
    
    if self.team_num == 1:
      return self.amount_bet * match.t1o - self.amount_bet
    elif self.team_num == 2:
      return self.amount_bet * match.t2o - self.amount_bet
    
  def get_team_and_payout(self):
    match = self.match

    team = ""
    payout = 0.0
    
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

  def short_to_string(self, session=None):
    if session is None:
      with Session.begin() as session:
        return self.short_to_string(session)
    
    (team, payout) = self.get_team_and_payout()

    return f"User: {self.user.username}, Team: {team}, Amount: {self.amount_bet}, Payout on Win: {int(math.floor(payout))}"
  
  def short_to_hidden_string(self, session=None):
    if session is None:
      with Session.begin() as session:
        return self.short_to_hidden_string(session)
      
    return f"User: {self.user.username}'s Hidden Bet on {self.t1} vs {self.t2}"
    
    
    
  def balance_to_string(self, balances):

    (team, winner) = self.get_team_and_winner()

    return f"{self.t1} vs {self.t2}, Bet on: {team}, Winner: {winner}, Amount bet: {self.amount_bet}, balance change: {math.floor(balances)}"

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
