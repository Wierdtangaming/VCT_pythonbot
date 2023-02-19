from sqlalchemy import Column, String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlaobjs import mapper_registry, Session
from utils import get_random_hex_color, mix_colors

@mapper_registry.mapped
class Tournament():
  
  __tablename__ = "tournament"
  
  name = Column(String(100), primary_key=True, nullable=False)
  vlr_code = Column(Integer)
  color_name = Column(String(32), ForeignKey("color.name"))
  color = relationship("Color", back_populates="tournaments")
  color_hex = Column(String(6))
  active = Column(Boolean)
  matches = relationship("Match", back_populates="tournament")
  bets = relationship("Bet", back_populates="tournament")
  
  def __init__(self, name, vlr_code, color):
    self.name = name
    self.vlr_code = vlr_code
    self.set_color(color)
    self.active = True
    
  def __repr__(self):
    return f"<Tournament {self.name}>"
        
  def set_color(self, color, session=None):
    if color is None:
      self.color = None
      self.color_name = None
      self.color_hex = get_random_hex_color()
    elif isinstance(color, str):
      self.color = None
      self.color_name = None
      self.color_hex = color
    else:
      self.color = color
      self.color_name = color.name
      self.color_hex = color.hex
    
    if session is not None:
      for match in self.matches:
        match.set_color(session)
      