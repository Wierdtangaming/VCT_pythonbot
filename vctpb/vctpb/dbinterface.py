from datetime import datetime
from pytz import timezone

from sqlaobjs import Session
from sqlalchemy import select, func

from DBMatch import Match
from DBUser import User
from DBBet import Bet
from Color import Color
from Channels import Channels

from configparser import ConfigParser

def get_date():
  central = timezone('US/Central')
  return datetime.now(central)



def get_all_db(table_name, session=None):
  if session is None:
    with Session.begin() as session:
      return session.scalars(select(eval(table_name))).all()
  else:
    return session.scalars(select(eval(table_name))).all()


def get_from_db(table_name, code, session=None):
  if session is None:
    with Session.begin() as session:
      return session.get(eval(table_name), code, populate_existing=True)
  else:
    return session.get(eval(table_name), code, populate_existing=True)
    
    
def get_mult_from_db(table_name, codes, session=None):
  if session is None:
    with Session.begin() as session:
      return get_mult_from_db(table_name, codes, session)
  else:
    if table_name == "Color":
      return session.scalars(select(Color).where(Color.name.in_(codes))).all()
    else:
      obj = eval(table_name)
      return session.scalars(select(obj).where(obj.code.in_(codes))).all()


def delete_from_db(ambig, table_name=None, session=None):
  if isinstance(ambig, str) or isinstance(ambig, int):
    code = ambig
    if session is None:
      with Session.begin() as session:
        session.delete(session.get(eval(table_name), code))
    else:
      session.delete(session.get(eval(table_name), code))
  else:
    if session is None:
      with Session.begin() as session:
        session.delete(ambig)
    else:
      session.delete(ambig)
  session.expire_all()
    
    
def add_to_db(obj, session=None):
  if session is None:
    with Session.begin() as session:
      session.add(obj)
  else:
    session.add(obj)
  session.expire_all()


def is_key_in_db(table_name, key, session=None):
  if session is None:
    with Session.begin() as session:
      return is_key_in_db(table_name, key, session)
  else:
    if table_name == "Color":
      return session.scalars(select(Color).where(Color.name == key)).one_or_none() is not None
    else:
      obj = eval(table_name)
      return session.scalars(select(obj).where(obj.code == key)).one_or_none() is not None
      
      
def get_channel_from_db(channel_name, session=None):
  if session is None:
    with Session.begin() as session:
      return get_channel_from_db(channel_name, session)
  else:
    channels = session.scalars(select(Channels)).one()
    if channel_name == "bet":
      return channels.bet_channel_id
    elif channel_name == "match":
      return channels.match_channel_id
    else:
      return None
                           
                          
def get_setting(setting_name):
  #setting_names: "discord_token", "github_token", "guild_ids", "override_savedata", "save_repo"
  configur = ConfigParser()
  configur.read('settings.ini')
  return configur.get("settings", setting_name)
  