import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")

engine = create_engine(db_url)

localSession = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = localSession()
    try:
        yield db
    finally:
        db.close()