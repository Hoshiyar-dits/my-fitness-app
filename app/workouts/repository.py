from datetime import date
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.workouts.models.workout import Workout

class WorkoutRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create(self, user_id: int, data: dict):
        try:
            workout = Workout(user_id=user_id, **data)
            self.db.add(workout)
            self.db.commit()
            self.db.refresh(workout)
            return workout
        except Exception:
            self.db.rollback()
            raise

    def get(self, user_id: int, workout_id: int):
        return self.db.query(Workout).filter(Workout.id == workout_id, Workout.user_id == user_id).first()

    def list(self, user_id: int, from_date: Optional[date], to_date: Optional[date], limit: int, offset: int):
        query = self.db.query(Workout).filter(Workout.user_id == user_id)
        if from_date:
            query = query.filter(Workout.workout_date >= from_date)
        if to_date:
            query = query.filter(Workout.workout_date <= to_date)
        return query.order_by(Workout.workout_date.desc(), Workout.id.desc()).offset(offset).limit(limit).all()

    def update(self, workout: Workout, data: dict):
        try:
            for field, value in data.items():
                setattr(workout, field, value)
            self.db.commit()
            self.db.refresh(workout)
            return workout
        except Exception:
            self.db.rollback()
            raise

    def delete(self, workout: Workout):
        try:
            self.db.delete(workout)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
