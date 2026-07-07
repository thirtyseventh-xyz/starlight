from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.models import Base
import os

engine = create_engine("postgresql+psycopg2://"+str(os.environ.get("POSTGRES_USER"))+":"+str(os.environ.get("POSTGRES_PASSWORD"))+"@"+str(os.environ.get("POSTGRES_IP"))+"/"+str(os.environ.get("POSTGRES_DB")))
# Base.metadata.create_all(engine) #dev function to init db, just use alembic migrations
SessionLocal = sessionmaker(bind=engine)