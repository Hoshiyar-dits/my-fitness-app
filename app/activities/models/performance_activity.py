from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Numeric, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.database.types import UTCDateTime, utcnow

class PerformanceActivity(Base):
    """A raw performance measurement. Units are fixed by column: metres, seconds, centimetres.
    Derived values (pace, speed) are calculated in app/activities/metrics.py, never stored."""
    __tablename__ = "performance_activities"
    __table_args__ = (Index("ix_performance_activities_user_type_date", "user_id", "activity_type", "activity_date"),)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    planned_workout_id = Column(BigInteger, ForeignKey("planned_workouts.id", ondelete="SET NULL"), nullable=True)
    activity_date = Column(Date, nullable=False)
    activity_type = Column(String(20), nullable=False)  # run, sprint, long_jump, high_jump
    distance_m = Column(Numeric(9, 2), nullable=True)  # run / sprint
    elapsed_seconds = Column(Numeric(9, 2), nullable=True)  # run / sprint
    jump_cm = Column(Numeric(6, 1), nullable=True)  # long jump distance or high jump height
    technique = Column(String(30), nullable=True)
    attempt_number = Column(SmallInteger, nullable=True)
    is_assessment = Column(Boolean, nullable=False, default=False)
    measurement_method = Column(String(30), nullable=True)
    conditions = Column(String(255), nullable=True)
    perceived_effort = Column(SmallInteger, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(UTCDateTime, nullable=False, default=utcnow)
    updated_at = Column(UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow)

    splits = relationship("ActivitySplit", order_by="ActivitySplit.split_number", cascade="all, delete-orphan", lazy="selectin")


class ActivitySplit(Base):
    """One segment of a run or sprint (segment distance and segment time, not cumulative)."""
    __tablename__ = "activity_splits"
    __table_args__ = (UniqueConstraint("activity_id", "split_number", name="uq_activity_splits_activity_number"),)

    id = Column(BigInteger, primary_key=True)
    activity_id = Column(BigInteger, ForeignKey("performance_activities.id", ondelete="CASCADE"), nullable=False)
    split_number = Column(SmallInteger, nullable=False)
    distance_m = Column(Numeric(9, 2), nullable=False)
    elapsed_seconds = Column(Numeric(9, 2), nullable=False)
