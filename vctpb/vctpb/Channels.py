from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from sqlaobjs import mapper_registry

@mapper_registry.mapped
class Channels():
  
  __tablename__ = "channels"
  
  bet_channel_id = Column(Integer, primary_key=True, nullable=False)
  match_channel_id = Column(Integer, nullable=False)
  
  
  def __init__(self, bet_channel_id, match_channel_id):
    self.bet_channel_id = bet_channel_id
    self.match_channel_id = match_channel_id
    
    
  def __repr__(self):
    return f"<Channels {self.bet_channel_id}, {self.match_channel_id}>"