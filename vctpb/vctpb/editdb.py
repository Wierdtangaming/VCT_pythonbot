from sqlalchemy import create_engine
from sqlinterface import add_column
from Bet import Bet
TestEngine = create_engine('sqlite:///testdata/savedata.db', future=True)

#add_column("bet", "hidden", "BOOLEAN", False, "false", engine=TestEngine)

#get the sqlinit for tabel
print(Bet.__table__, type(Bet.__table__))
#poetry run python vctpb/editdb.py