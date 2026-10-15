from sqlalchemy import Column, Integer, BigInteger, String, Date, Numeric, DateTime, ForeignKey, func
from app.database.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    date_of_birth = Column(Date, nullable=False)
    height_cm = Column(Numeric(5, 2), nullable=False)
    gender = Column(String(30), nullable=True)
    activity_level = Column(String(30), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
