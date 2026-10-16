from datetime import date
from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.workouts.models.workout import Workout
from app.meals.models.meal import Meal
from app.body_metrics.models.body_metric import BodyMetric

class ProgressRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def workout_totals_by_day(self, user_id: int, start: date, end: date):
        return (
            self.db.query(
                Workout.workout_date.label("day"),
                func.count(Workout.id).label("count"),
                func.coalesce(func.sum(Workout.duration_minutes), 0).label("minutes"),
                func.coalesce(func.sum(Workout.calories_burned), 0).label("calories"),
            )
            .filter(Workout.user_id == user_id, Workout.workout_date.between(start, end))
            .group_by(Workout.workout_date)
            .all()
        )

    def meal_totals_by_day(self, user_id: int, start: date, end: date):
        return (
            self.db.query(
                Meal.meal_date.label("day"),
                func.count(Meal.id).label("count"),
                func.coalesce(func.sum(Meal.calories), 0).label("calories"),
                func.coalesce(func.sum(Meal.protein_g), 0).label("protein"),
                func.coalesce(func.sum(Meal.carbs_g), 0).label("carbs"),
                func.coalesce(func.sum(Meal.fat_g), 0).label("fat"),
            )
            .filter(Meal.user_id == user_id, Meal.meal_date.between(start, end))
            .group_by(Meal.meal_date)
            .all()
        )

    def weights_in_range(self, user_id: int, start: date, end: date):
        return (
            self.db.query(BodyMetric.log_date, BodyMetric.weight_kg)
            .filter(BodyMetric.user_id == user_id, BodyMetric.log_date.between(start, end))
            .all()
        )

    def latest_body_metric(self, user_id: int, on_or_before: date):
        return (
            self.db.query(BodyMetric)
            .filter(BodyMetric.user_id == user_id, BodyMetric.log_date <= on_or_before)
            .order_by(BodyMetric.log_date.desc())
            .first()
        )

    def recent_workout_dates(self, user_id: int, on_or_before: date, limit: int = 366):
        rows = (
            self.db.query(Workout.workout_date)
            .filter(Workout.user_id == user_id, Workout.workout_date <= on_or_before)
            .distinct()
            .order_by(Workout.workout_date.desc())
            .limit(limit)
            .all()
        )
        return [row[0] for row in rows]
