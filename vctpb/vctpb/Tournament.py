from sqlalchemy import Column, String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship

from sqlaobjs import mapper_registry

@mapper_registry.mapped
class Tournament():
  
  __tablename__ = "tournament"
  
  name = Column(String(100), primary_key=True, nullable=False)
  vlr_code = Column(Integer)
  color_name = Column(String(32), ForeignKey("color.name"))
  color = relationship("Color", back_populates="tournaments")
  color_hex = Column(String(6))
  active = Column(Boolean, default=1)
  
  def __init__(self, name, color):
    self.name = name
    self.set_color(color)
    
  def __repr__(self):
    return f"<Tournament {self.name}>"
        
  def set_color(self, color):
    if isinstance(color, str):
      self.color = None
      self.color_name = None
      self.color_hex = color
      return
    
    self.color = color
    self.color_name = color.name
    self.color_hex = color.hex