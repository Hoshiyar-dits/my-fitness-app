from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Numeric, Boolean, JSON, ForeignKey, UniqueConstraint
from app.database.database import Base
from app.database.types import UTCDateTime, utcnow

class DailyCheckin(Base):
    """Daily recovery check-in. Weight / body fat given with a check-in are stored in body_metrics."""
    __tablename__ = "daily_checkins"
    __table_args__ = (UniqueConstraint("user_id", "checkin_date", name="uq_daily_checkins_user_date"),)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    checkin_date = Column(Date, nullable=False)
    sleep_hours = Column(Numeric(3, 1), nullable=True)
    sleep_quality = Column(SmallInteger, nullable=True)  # 1 (very poor) - 5 (very good)
    energy_level = Column(SmallInteger, nullable=True)  # 1 - 5
    fatigue_level = Column(SmallInteger, nullable=True)  # 1 (fresh) - 5 (exhausted)
    soreness_level = Column(SmallInteger, nullable=True)  # 1 (none) - 5 (severe)
    pain_level = Column(SmallInteger, nullable=True)  # 0 - 10
    pain_location = Column(String(255), nullable=True)
    warning_symptoms = Column(JSON, nullable=False, default=list)
    workout_completed = Column(Boolean, nullable=True)
    perceived_effort = Column(SmallInteger, nullable=True)  # RPE 1 - 10
    resting_heart_rate = Column(SmallInteger, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(UTCDateTime, nullable=False, default=utcnow)
    updated_at = Column(UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow)
