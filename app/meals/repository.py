from datetime import date
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.meals.models.meal import Meal

class MealRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create(self, user_id: int, data: dict):
        try:
            meal = Meal(user_id=user_id, **data)
            self.db.add(meal)
            self.db.commit()
            self.db.refresh(meal)
            return meal
        except Exception:
            self.db.rollback()
            raise

    def get(self, user_id: int, meal_id: int):
        return self.db.query(Meal).filter(Meal.id == meal_id, Meal.user_id == user_id).first()

    def list(self, user_id: int, from_date: Optional[date], to_date: Optional[date], limit: int, offset: int):
        query = self.db.query(Meal).filter(Meal.user_id == user_id)
        if from_date:
            query = query.filter(Meal.meal_date >= from_date)
        if to_date:
            query = query.filter(Meal.meal_date <= to_date)
        return query.order_by(Meal.meal_date.desc(), Meal.id.desc()).offset(offset).limit(limit).all()

    def update(self, meal: Meal, data: dict):
        try:
            for field, value in data.items():
                setattr(meal, field, value)
            self.db.commit()
            self.db.refresh(meal)
            return meal
        except Exception:
            self.db.rollback()
            raise

    def delete(self, meal: Meal):
        try:
            self.db.delete(meal)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
