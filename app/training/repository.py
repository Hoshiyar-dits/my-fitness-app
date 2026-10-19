from datetime import date
from typing import Iterable, List, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.training.exercise_catalog import CATALOG_BY_NAME
from app.training.models.training import Exercise, TrainingProgram, PlannedWorkout

OPEN_PROGRAM_STATUSES = ("active", "awaiting_clearance")
LIVE_PLAN_STATUSES = ("proposed", "confirmed")


class ExerciseRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def list(self, category: Optional[str] = None):
        query = self.db.query(Exercise)
        if category:
            query = query.filter(Exercise.category == category)
        return query.order_by(Exercise.category, Exercise.name).all()

    def get_many(self, ids: Iterable[int]):
        ids = set(ids)
        return {e.id: e for e in self.db.query(Exercise).filter(Exercise.id.in_(ids)).all()} if ids else {}

    def get_by_name(self, name: str) -> Exercise:
        """Catalog lookup. Adds the entry from exercise_catalog.py if it is missing (no commit; the caller commits)."""
        exercise = self.db.query(Exercise).filter(Exercise.name == name).first()
        if exercise is None:
            category, high_impact, equipment, description = CATALOG_BY_NAME[name]
            exercise = Exercise(name=name, category=category, is_high_impact=high_impact,
                                required_equipment=equipment, description=description)
            self.db.add(exercise)
            self.db.flush()
        return exercise


class ProgramRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get(self, user_id: int, program_id: int):
        return self.db.query(TrainingProgram).filter(TrainingProgram.id == program_id, TrainingProgram.user_id == user_id).first()

    def current(self, user_id: int):
        """The open program, or else the most recent one."""
        open_program = (
            self.db.query(TrainingProgram)
            .filter(TrainingProgram.user_id == user_id, TrainingProgram.status.in_(OPEN_PROGRAM_STATUSES))
            .order_by(TrainingProgram.start_date.desc(), TrainingProgram.id.desc())
            .first()
        )
        if open_program:
            return open_program
        return (
            self.db.query(TrainingProgram)
            .filter(TrainingProgram.user_id == user_id)
            .order_by(TrainingProgram.start_date.desc(), TrainingProgram.id.desc())
            .first()
        )

    def open_program(self, user_id: int):
        return (
            self.db.query(TrainingProgram)
            .filter(TrainingProgram.user_id == user_id, TrainingProgram.status.in_(OPEN_PROGRAM_STATUSES))
            .first()
        )

    def save_all(self, objects: List):
        """Adds and commits several new rows (a program with its sessions, goals, baseline measurements) in one transaction."""
        try:
            self.db.add_all(objects)
            self.db.commit()
            for obj in objects:
                self.db.refresh(obj)
            return objects
        except Exception:
            self.db.rollback()
            raise

    def update(self, program: TrainingProgram, data: dict):
        try:
            for field, value in data.items():
                setattr(program, field, value)
            self.db.commit()
            self.db.refresh(program)
            return program
        except Exception:
            self.db.rollback()
            raise

    def delete(self, program: TrainingProgram):
        try:
            self.db.rollback()  # discard anything half-added by the failed step
            self.db.delete(program)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise


class PlanRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get(self, user_id: int, plan_id: int):
        return self.db.query(PlannedWorkout).filter(PlannedWorkout.id == plan_id, PlannedWorkout.user_id == user_id).first()

    def list(self, user_id: int, from_date: Optional[date], to_date: Optional[date], statuses: Optional[Iterable[str]],
             limit: int = 200, offset: int = 0):
        query = self.db.query(PlannedWorkout).filter(PlannedWorkout.user_id == user_id)
        if from_date:
            query = query.filter(PlannedWorkout.plan_date >= from_date)
        if to_date:
            query = query.filter(PlannedWorkout.plan_date <= to_date)
        if statuses:
            query = query.filter(PlannedWorkout.status.in_(list(statuses)))
        return query.order_by(PlannedWorkout.plan_date, PlannedWorkout.id).offset(offset).limit(limit).all()

    def confirmed_on(self, user_id: int, day: date):
        return self.list(user_id, day, day, ["confirmed"])

    def for_program(self, program_id: int):
        return (
            self.db.query(PlannedWorkout)
            .filter(PlannedWorkout.program_id == program_id)
            .order_by(PlannedWorkout.plan_date, PlannedWorkout.id)
            .all()
        )

    def add(self, plan: PlannedWorkout):
        try:
            self.db.add(plan)
            self.db.commit()
            self.db.refresh(plan)
            return plan
        except Exception:
            self.db.rollback()
            raise

    def update(self, plan: PlannedWorkout, data: dict):
        try:
            for field, value in data.items():
                setattr(plan, field, value)
            self.db.commit()
            self.db.refresh(plan)
            return plan
        except Exception:
            self.db.rollback()
            raise

    def complete(self, plan: PlannedWorkout, data: dict, workout, performed: Iterable):
        """Marks the plan done, logs the matching workout and the performed exercises in one transaction."""
        try:
            self.db.add(workout)
            self.db.flush()
            for obj in performed:
                self.db.add(obj)
            for field, value in data.items():
                setattr(plan, field, value)
            plan.workout_id = workout.id
            self.db.commit()
            self.db.refresh(plan)
            return plan
        except Exception:
            self.db.rollback()
            raise

    def update_many(self, plans: Iterable[PlannedWorkout], data: dict):
        try:
            for plan in plans:
                for field, value in data.items():
                    setattr(plan, field, value)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
