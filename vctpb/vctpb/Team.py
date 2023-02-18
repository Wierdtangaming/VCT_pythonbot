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
  
  
  def __init__(self, name, vrl_code, color = None):
    self.name = name
    self.vrl_code = vrl_code
    if color is None:
      color = get_random_hex_color()
    self.set_color(color)
    
    
  def __repr__(self):
    return f"<Team {self.name}, code: {self.vlr_code}>"
        
  def set_color(self, color):
    if isinstance(color, str):
      self.color = None
      self.color_name = None
      self.color_hex = color
      return
    
    self.color = color
    self.color_name = color.name
    self.color_hex = color.hex
