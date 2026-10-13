from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP
from app.database.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255),nullable=False,unique=True)
    mobile = Column(String(255), nullable=True)
    status = Column(Enum("0","1"),nullable=False, default="1")
    photo = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)