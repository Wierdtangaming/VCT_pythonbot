from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqltypes import JSONLIST, DECIMAL
from sqlalchemy.ext.mutable import MutableList
from sqlaobjs import mapper_registry

@mapper_registry.mapped
class Match():
  
  __tablename__ = "match"
  
  code = Column(String(8), primary_key = True, nullable=False)
  t1 = Column(String(50), nullable=False)
  t2 = Column(String(50), nullable=False)
  t1o = Column(DECIMAL(5, 3), nullable=False)
  t2o = Column(DECIMAL(5, 3), nullable=False)
  t1oo = Column(DECIMAL(5, 3), nullable=False)
  t2oo = Column(DECIMAL(5, 3), nullable=False)
  tournament_name = Column(String(100), nullable=False)
  odds_source = Column(String(50), nullable=False)
  winner = Column(Integer, nullable=False)
  color_name = Column(String(32), ForeignKey("color.name"))
  color = relationship("Color", back_populates="matches")
  color_hex = Column(String(6), nullable=False)
  creator_id = Column(Integer, ForeignKey("user.code"))
  creator = relationship("User", back_populates="matches")
  date_created = Column(DateTime(timezone = True), nullable=False)
  date_winner = Column(DateTime(timezone = True), nullable=False)
  date_closed = Column(DateTime(timezone = True), nullable=False)
  bets = relationship("Bet", back_populates="match", cascade="all, delete")
  message_ids = Column(MutableList.as_mutable(JSONLIST), nullable=False) #array of int
  
  def __init__(self, code, t1, t2, t1o, t2o, t1oo, t2oo, tournament_name, odds_source, color, creator_id, date_created):


    self.code = code
    self.t1 = t1
    self.t2 = t2
    self.t1o = t1o
    self.t2o = t2o
    self.t1oo = t1oo
    self.t2oo = t2oo

    self.tournament_name = tournament_name
    
    self.odds_source = odds_source
    
    self.winner = 0

    self.set_color(color)
    
    #id of user that created match
    self.creator_id = creator_id

    self.date_created = date_created

    self.date_winner = None
    self.date_closed = None
    
    
    self.bet_ids = []
    self.message_ids = []
  
  def __init__(self, code, t1, t2, t1o, t2o, t1oo, t2oo, tournament_name, winner, odds_source, color, creator_id, date_created, date_winner, date_closed, bet_ids, message_ids):
    self.code = code
    self.t1 = t1
    self.t2 = t2
    self.t1o = t1o
    self.t2o = t2o
    self.t1oo = t1oo
    self.t2oo = t2oo
    self.tournament_name = tournament_name
    self.winner = winner
    self.odds_source = odds_source
    self.set_color(color)
    self.creator_id = creator_id
    self.date_created = date_created
    self.date_winner = date_winner
    self.date_closed = date_closed
    self.bet_ids = bet_ids
    self.message_ids = message_ids
  
  def set_color(self, color):
    if isinstance(color, str):
      self.color_name = None
      self.color_hex = color
      return
    
    self.color_name = color.name
    self.color_hex = color.hex
  
  def __repr__(self):
    return f"<Match {self.code}>"
  
  def to_string(self):
    date_formatted = self.date_created.strftime("%d/%m/%Y at %H:%M:%S")
    return "Teams: " + str(self.t1) + " vs " + str(self.t2) + ", Odds: " + str(self.t1o) + " / " + str(self.t2o) +  ", Old Odds: " + str(self.t1oo) + " / " + str(self.t2oo) + ", Tournament Name: " + str(self.tournament_name) + ", Odds Source: " + str(self.odds_source) + ", Created On: " + str(date_formatted) + ", Bet IDs: " + str(self.bet_ids) + ", Date Closed: " + str(self.date_closed) + ", Winner: " + str(self.winner) + ", Identifyer: " + str(self.code) + ", Message IDs: " + str(self.message_ids)


  def short_to_string(self):
    return "Teams: " + str(self.t1) + " vs " + str(self.t2) + ", Odds: " + str(self.t1o) + " / " + str(self.t2o)

  def winner_name(self):
    if self.winner == 0:
      return "None"
    elif self.winner == 1:
      return self.t1
    else:
      return self.t2

  def basic_to_string(self):
    return f"Match: {self.code}, Teams: {self.t1} vs {self.t2}, Odds: {self.t1o} vs {self.t2o}, Tournament Name: {self.tournament_name}"
  
  
  
def is_valid_match(code, t1, t2, t1o, t2o, t1oo, t2oo, tournament_name, odds_source, winner, color, creator_id, date_created, date_winner, date_closed, bet_ids, message_ids):
  errors = [False for _ in range(17)]
  if isinstance(code, str) == False or len(code) != 8:
    errors[0] = True
    print("code", code, type(code))
  if isinstance(t1, str) == False or len(t1) > 50:
    errors[1] = True
    print("t1", t1, type(t1))
  if isinstance(t2, str) == False or len(t2) > 50:
    errors[2] = True
    print("t2", t2, type(t2))
  if isinstance(t1o, Decimal) == False or t1o < 0:
    errors[3] = True
    print("t1o", t1o, type(t1o))
  if isinstance(t2o, Decimal) == False or t2o < 0:
    errors[4] = True
    print("t2o", t2o, type(t2o))
  if isinstance(t1oo, Decimal) == False or t1oo < 0:
    errors[5] = True
    print("t1oo", t1oo, type(t1oo))
  if isinstance(t2oo, Decimal) == False or t2oo < 0:
    errors[6] = True
    print("t2oo", t2oo, type(t2oo))
  if isinstance(tournament_name, str) == False or len(tournament_name) > 100:
    errors[7] = True
    print("tournament_name", tournament_name, type(tournament_name))
  if isinstance(odds_source, str) == False or len(odds_source) > 50:
    errors[8] = True
    print("odds_source", odds_source, type(odds_source))
  if isinstance(winner, int) == False or winner < 0 or winner > 2:
    errors[9] = True
    print("winner", winner, type(winner))
  if isinstance(color, str) == False or len(color) > 6:
    errors[10] = True
    print("color", color, type(color))
  if isinstance(creator_id, int) == False:
    errors[11] = True
    print("creator", creator_id, type(creator_id))
  if isinstance(date_created, datetime) == False:
    errors[12] = True
    print("date_created", date_created, type(date_created))
  if isinstance(date_winner, datetime) == False:
    errors[13] = True
    print("date_winner", date_winner, type(date_winner))
  if isinstance(date_closed, datetime) == False:
    errors[14] = True
    print("date_closed", date_closed, type(date_closed))
  if isinstance(bet_ids, list) == False:
    errors[15] = True
    print("bet_ids", bet_ids, type(bet_ids))
  if isinstance(message_ids, list) == False:
    errors[16] = True
    print("message_ids", message_ids, type(message_ids))

  return errors
