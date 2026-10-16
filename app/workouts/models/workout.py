from sqlalchemy import Column, Integer, BigInteger, String, Text, Date, DateTime, ForeignKey, Index, func
from app.database.database import Base

class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = (Index("ix_workouts_user_date", "user_id", "workout_date"),)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workout_date = Column(Date, nullable=False)
    workout_type = Column(String(30), nullable=False)
    name = Column(String(255), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    calories_burned = Column(Integer, nullable=True)
    intensity = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
