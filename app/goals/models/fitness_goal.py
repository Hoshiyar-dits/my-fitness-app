from sqlalchemy import Column, Integer, BigInteger, String, Date, Numeric, ForeignKey, Index
from app.database.database import Base
from app.database.types import UTCDateTime, utcnow

class FitnessGoal(Base):
    __tablename__ = "fitness_goals"
    __table_args__ = (Index("ix_fitness_goals_user_status", "user_id", "status"),)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    program_id = Column(BigInteger, ForeignKey("training_programs.id", ondelete="SET NULL"), nullable=True)
    goal_type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=True)
    # each goal type has exactly one allowed unit (see GOAL_UNITS), so values of a type are always comparable
    unit = Column(String(10), nullable=False)
    reference_distance_m = Column(Numeric(9, 2), nullable=True)  # timed goals: the distance the time refers to
    technique = Column(String(30), nullable=True)  # jump goals: e.g. standing / run_up
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)
    baseline_value = Column(Numeric(10, 3), nullable=True)
    target_value = Column(Numeric(10, 3), nullable=False)
    current_value = Column(Numeric(10, 3), nullable=True)
    current_value_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(UTCDateTime, nullable=False, default=utcnow)
    updated_at = Column(UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow)
