from sqlalchemy.orm import registry
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


mapper_registry = registry()
Engine = create_engine('sqlite:///savedata.db', future=True)
Session = sessionmaker(bind=Engine, future=True, expire_on_commit=False)