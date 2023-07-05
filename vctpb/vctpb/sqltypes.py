from sqlalchemy.types import TypeDecorator, VARCHAR, String
import pickle
from decimal import Decimal
import time
from sqlalchemy.ext.mutable import MutableList
from discord import Message, Interaction

class MsgMutableList(MutableList):
  async def append(self, ambig):
    if issubclass(type(ambig), Message):
      return super().append((ambig.id, ambig.channel.id))
    elif issubclass(type(ambig), Interaction):
      ambig = await ambig.original_response()
      return super().append((ambig.id, ambig.channel.id))
    else:
      return super().append(ambig)

class JSONList(TypeDecorator):
  impl = String

  def process_bind_param(self, value, dialect):
    if value is not None:
      value = pickle.dumps(value)
    return value

  def process_result_value(self, value, dialect):
    if value is not None:
      value = pickle.loads(value)
    return value
  
  
class DECIMAL(TypeDecorator):
  impl = String
  
  def load_dialect_impl(self, dialect):
    return dialect.type_descriptor(VARCHAR(6))
  
  def process_bind_param(self, value, dialect):
    if value is not None:
      value = str(value)
      if len(value) > 6:
        f, s = value.split('.')
        if len(f) > 2:
          f = "99"
        if len(s) > 3:
          s = s[:3] 
        value = Decimal(f + '.' + s)
      
    return str(value)
  
  def process_result_value(self, value, dialect):
    if value is not None:
      value
    return Decimal(value)
  