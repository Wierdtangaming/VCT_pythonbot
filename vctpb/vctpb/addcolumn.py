from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Engine = create_engine('sqlite:///testdata/savedata.db', future=True)

with Engine.begin() as connection:
  connection.execute( text(
"""
ALTER TABEL bet
ADD COLUMN hidden BOOLEAN 
NOT NULL DEFAULT 0
"""
  ))

 