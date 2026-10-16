from sqlalchemy import Column, Integer, BigInteger, String, Text, Date, Numeric, DateTime, ForeignKey, Index, func
from app.database.database import Base

class Meal(Base):
    __tablename__ = "meals"
    __table_args__ = (Index("ix_meals_user_date", "user_id", "meal_date"),)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    meal_date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    calories = Column(Integer, nullable=False)
    protein_g = Column(Numeric(6, 2), nullable=True)
    carbs_g = Column(Numeric(6, 2), nullable=True)
    fat_g = Column(Numeric(6, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
