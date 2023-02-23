import discord

from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship

from sqlaobjs import mapper_registry, Session
#from Match import Match
from utils import get_random_hex_color

@mapper_registry.mapped
class Team():
  
  __tablename__ = "team"
  
  name = Column(String(50), primary_key=True, nullable=False)
  vlr_code = Column(Integer)
  color_name = Column(String(32), ForeignKey("color.name"))
  color = relationship("Color", back_populates="teams")
  color_hex = Column(String(6))
  
  bets_as_t1 = relationship("Bet", foreign_keys="Bet.t1", back_populates="team1")
  bets_as_t2 = relationship("Bet", foreign_keys="Bet.t2", back_populates="team2")
  @property
  def bets(self):
    return self.bets_as_t1 + self.bets_as_t2
  
  matches_as_t1 = relationship("Match", foreign_keys="Match.t1", back_populates="team1")
  matches_as_t2 = relationship("Match", foreign_keys="Match.t2", back_populates="team2")
  @property
  def matches(self):
    return self.matches_as_t1 + self.matches_as_t2
  
  
  
  def __init__(self, name, vlr_code, color = None):
    self.name = name
    self.vlr_code = vlr_code
    if color is None:
      color = get_random_hex_color()
    self.set_color(color)
    
    
  def __repr__(self):
    return f"<Team {self.name}, code: {self.vlr_code}>"
        
  def set_color(self, color, session = None):
    if color is None:
      self.color = None
      self.color_name = None
      self.color_hex = get_random_hex_color()
    elif isinstance(color, str):
      if self.color_hex == color:
        return
      self.color = None
      self.color_name = None
      self.color_hex = color
    else:
      self.color = color
      self.color_name = color.name
      self.color_hex = color.hex
    
    if session is not None:
      for bet in self.bets:
        bet.set_color(session)
      for match in self.matches:
        match.set_color(session)
        
  def set_name(self, name, session):
    for bet in self.bets_as_t1:
      bet.t1 = self.name
    for bet in self.bets_as_t2:
      bet.t2 = self.name
    for match in self.matches_as_t1:
      match.t1 = self.name
    for match in self.matches_as_t2:
      match.t2 = self.name
    self.name = name
  
  def merge(self, other, session):
    # overrides color of other to update the best and matches it is in
    print("\n\n\n>>>>>>>>>>>>>>>>>>>>>>>>>\n\n\n")
    if self.color is None:
      other.set_color(self.color_hex, session)
    else:
      other.set_color(self.color, session)
      print(self.name)
    print("\n\n\n---------------------------\n\n\n")
    for bet in other.bets_as_t1:
      bet.t1 = self.name
    for bet in other.bets_as_t2:
      bet.t2 = self.name
    print("\n\n\n++++++++++++++++++++++++++\n\n\n")
    for match in other.matches_as_t1:
      match.t1 = self.name
    for match in other.matches_as_t2:
      match.t2 = self.name
    print("\n\n\n==========================\n\n\n")
    session.delete(other)
