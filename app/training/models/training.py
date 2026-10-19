from sqlalchemy import (
    Column, Integer, BigInteger, SmallInteger, String, Text, Date, Numeric, Boolean, JSON, ForeignKey, Index,
)
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.database.types import UTCDateTime, utcnow


class Exercise(Base):
    """Shared exercise catalog (not user-owned). Seeded by migration from app/training/exercise_catalog.py."""
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(30), nullable=False)
    description = Column(Text, nullable=True)
    is_high_impact = Column(Boolean, nullable=False, default=False)
    required_equipment = Column(String(50), nullable=True)


class TrainingProgram(Base):
    """A 25-day training cycle plus the onboarding assessment it was generated from."""
    __tablename__ = "training_programs"
    __table_args__ = (Index("ix_training_programs_user_status", "user_id", "status"),)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(30), nullable=False)
    experience_level = Column(String(20), nullable=False)
    training_background = Column(Text, nullable=True)
    available_minutes_per_day = Column(SmallInteger, nullable=False)
    equipment = Column(JSON, nullable=False, default=list)
    injury_history = Column(Text, nullable=True)
    current_pain = Column(Text, nullable=True)
    medical_restrictions = Column(Text, nullable=True)
    medical_clearance_confirmed = Column(Boolean, nullable=False, default=False)
    assessment_run_distance_m = Column(Numeric(9, 2), nullable=False)
    assessment_sprint_distance_m = Column(Numeric(6, 2), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(UTCDateTime, nullable=False, default=utcnow)
    updated_at = Column(UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow)


class PlannedWorkout(Base):
    """One planned session. `status` says whether it is only a suggestion (proposed) or accepted (confirmed);
    `completion_status` says what the user actually did."""
    __tablename__ = "planned_workouts"
    __table_args__ = (Index("ix_planned_workouts_user_date", "user_id", "plan_date"),)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    program_id = Column(BigInteger, ForeignKey("training_programs.id", ondelete="CASCADE"), nullable=True)
    plan_date = Column(Date, nullable=False)
    day_number = Column(SmallInteger, nullable=True)
    training_phase = Column(String(30), nullable=True)
    session_type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    warm_up = Column(Text, nullable=True)
    cool_down = Column(Text, nullable=True)
    intensity = Column(String(20), nullable=False)
    estimated_duration_minutes = Column(SmallInteger, nullable=False)
    is_high_impact = Column(Boolean, nullable=False, default=False)
    source = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    confirmed_at = Column(UTCDateTime, nullable=True)
    adjustment_reason = Column(Text, nullable=True)
    based_on_plan_id = Column(BigInteger, ForeignKey("planned_workouts.id", ondelete="SET NULL"), nullable=True)
    completion_status = Column(String(20), nullable=False, default="pending")
    skip_reason = Column(Text, nullable=True)
    actual_duration_minutes = Column(SmallInteger, nullable=True)
    perceived_effort = Column(SmallInteger, nullable=True)
    completion_notes = Column(Text, nullable=True)
    completed_at = Column(UTCDateTime, nullable=True)
    workout_id = Column(BigInteger, ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(UTCDateTime, nullable=False, default=utcnow)
    updated_at = Column(UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow)

    exercises = relationship(
        "PlannedExercise", order_by="PlannedExercise.position", cascade="all, delete-orphan", lazy="selectin",
    )
    performed_exercises = relationship(
        "PerformedExercise", order_by="PerformedExercise.id", cascade="all, delete-orphan", lazy="selectin",
    )


class PlannedExercise(Base):
    __tablename__ = "planned_exercises"

    id = Column(BigInteger, primary_key=True)
    planned_workout_id = Column(BigInteger, ForeignKey("planned_workouts.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    position = Column(SmallInteger, nullable=False)
    sets = Column(SmallInteger, nullable=True)
    reps = Column(SmallInteger, nullable=True)
    distance_m = Column(Numeric(9, 2), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    rest_seconds = Column(Integer, nullable=True)
    effort = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    exercise = relationship("Exercise", lazy="joined")

    @property
    def exercise_name(self) -> str:
        return self.exercise.name


class PerformedExercise(Base):
    """What the user actually did for an exercise in a planned session (volume actually performed)."""
    __tablename__ = "performed_exercises"

    id = Column(BigInteger, primary_key=True)
    planned_workout_id = Column(BigInteger, ForeignKey("planned_workouts.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    sets = Column(SmallInteger, nullable=True)
    reps = Column(SmallInteger, nullable=True)
    distance_m = Column(Numeric(9, 2), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    load_kg = Column(Numeric(6, 2), nullable=True)
    notes = Column(Text, nullable=True)

    exercise = relationship("Exercise", lazy="joined")

    @property
    def exercise_name(self) -> str:
        return self.exercise.name
