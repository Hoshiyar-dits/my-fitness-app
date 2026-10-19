from sqlalchemy import Column, Integer, BigInteger, String, Text, Date, JSON, ForeignKey, UniqueConstraint
from app.database.database import Base
from app.database.types import UTCDateTime, utcnow

class DailyAnalysis(Base):
    """End-of-day review: what was planned vs done, readiness decision for tomorrow and why.
    `source_refs` records the ids of the rows the analysis was computed from."""
    __tablename__ = "daily_analyses"
    __table_args__ = (UniqueConstraint("user_id", "analysis_date", name="uq_daily_analyses_user_date"),)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    program_id = Column(BigInteger, ForeignKey("training_programs.id", ondelete="SET NULL"), nullable=True)
    analysis_date = Column(Date, nullable=False)
    readiness = Column(String(30), nullable=False)
    summary = Column(Text, nullable=False)
    reasons = Column(JSON, nullable=False, default=list)
    metrics = Column(JSON, nullable=False, default=dict)
    source_refs = Column(JSON, nullable=False, default=dict)
    recommendation = Column(Text, nullable=True)
    safety_message = Column(Text, nullable=True)
    generated_by = Column(String(20), nullable=False, default="rules")
    proposed_plan_id = Column(BigInteger, ForeignKey("planned_workouts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(UTCDateTime, nullable=False, default=utcnow)
    updated_at = Column(UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow)
