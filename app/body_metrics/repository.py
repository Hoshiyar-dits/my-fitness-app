from datetime import date
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.body_metrics.models.body_metric import BodyMetric

class BodyMetricRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_by_date(self, user_id: int, log_date: date):
        return self.db.query(BodyMetric).filter(BodyMetric.user_id == user_id, BodyMetric.log_date == log_date).first()

    def upsert(self, user_id: int, data: dict):
        try:
            metric = self.get_by_date(user_id, data["log_date"])
            if metric:
                for field, value in data.items():
                    setattr(metric, field, value)
            else:
                metric = BodyMetric(user_id=user_id, **data)
                self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            return metric
        except Exception:
            self.db.rollback()
            raise

    def list(self, user_id: int, from_date: Optional[date], to_date: Optional[date], limit: int):
        query = self.db.query(BodyMetric).filter(BodyMetric.user_id == user_id)
        if from_date:
            query = query.filter(BodyMetric.log_date >= from_date)
        if to_date:
            query = query.filter(BodyMetric.log_date <= to_date)
        return query.order_by(BodyMetric.log_date.desc()).limit(limit).all()

    def delete(self, metric: BodyMetric):
        try:
            self.db.delete(metric)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
