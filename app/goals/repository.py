from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.goals.models.fitness_goal import FitnessGoal

class GoalRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create(self, user_id: int, data: dict):
        try:
            goal = FitnessGoal(user_id=user_id, **data)
            self.db.add(goal)
            self.db.commit()
            self.db.refresh(goal)
            return goal
        except Exception:
            self.db.rollback()
            raise

    def get(self, user_id: int, goal_id: int):
        return self.db.query(FitnessGoal).filter(FitnessGoal.id == goal_id, FitnessGoal.user_id == user_id).first()

    def list(self, user_id: int, status: Optional[str], limit: int, offset: int):
        query = self.db.query(FitnessGoal).filter(FitnessGoal.user_id == user_id)
        if status:
            query = query.filter(FitnessGoal.status == status)
        return query.order_by(FitnessGoal.target_date, FitnessGoal.id).offset(offset).limit(limit).all()

    def active_of_type(self, user_id: int, goal_type: str):
        return (
            self.db.query(FitnessGoal)
            .filter(FitnessGoal.user_id == user_id, FitnessGoal.goal_type == goal_type, FitnessGoal.status == "active")
            .all()
        )

    def update(self, goal: FitnessGoal, data: dict):
        try:
            for field, value in data.items():
                setattr(goal, field, value)
            self.db.commit()
            self.db.refresh(goal)
            return goal
        except Exception:
            self.db.rollback()
            raise
