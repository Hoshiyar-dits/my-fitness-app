from datetime import date
from typing import Iterable, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.activities.models.performance_activity import PerformanceActivity, ActivitySplit

class ActivityRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create(self, user_id: int, data: dict, splits: list):
        try:
            activity = PerformanceActivity(user_id=user_id, **data)
            activity.splits = [ActivitySplit(split_number=i, **split) for i, split in enumerate(splits, start=1)]
            self.db.add(activity)
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except Exception:
            self.db.rollback()
            raise

    def list(self, user_id: int, types: Optional[Iterable[str]], from_date: Optional[date], to_date: Optional[date],
             limit: int = 500, offset: int = 0):
        query = self.db.query(PerformanceActivity).filter(PerformanceActivity.user_id == user_id)
        if types:
            query = query.filter(PerformanceActivity.activity_type.in_(list(types)))
        if from_date:
            query = query.filter(PerformanceActivity.activity_date >= from_date)
        if to_date:
            query = query.filter(PerformanceActivity.activity_date <= to_date)
        return query.order_by(PerformanceActivity.activity_date.desc(), PerformanceActivity.id.desc()).offset(offset).limit(limit).all()
