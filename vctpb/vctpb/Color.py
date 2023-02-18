from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from sqlaobjs import mapper_registry

@mapper_registry.mapped
class Color():
  
  __tablename__ = "color"
  
  name = Column(String(32), primary_key=True, nullable=False)
  hex = Column(String(6), nullable=False)
  users = relationship("User", back_populates="color")
  tournaments = relationship("Tournament", back_populates="color")
  teams = relationship("Team", back_populates="color")
  
  
  def __init__(self, name, hex):
    self.name = name
    self.hex = hex
    
    
  def __repr__(self):
    return f"<Color {self.name}, {self.hex}>"