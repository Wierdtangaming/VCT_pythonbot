from sqlalchemy.orm import sessionmaker, registry
from sqlalchemy import create_engine


mapper_registry = registry()
Engine = create_engine('sqlite:///savedata/savedata.db', future=True)
Session = sessionmaker(bind=Engine, future=True, expire_on_commit=False)