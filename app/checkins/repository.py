from datetime import date
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.checkins.models.daily_checkin import DailyCheckin

class CheckinRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create(self, user_id: int, data: dict):
        try:
            checkin = DailyCheckin(user_id=user_id, **data)
            self.db.add(checkin)
            self.db.commit()
            self.db.refresh(checkin)
            return checkin
        except Exception:
            self.db.rollback()
            raise

    def get(self, user_id: int, checkin_id: int):
        return self.db.query(DailyCheckin).filter(DailyCheckin.id == checkin_id, DailyCheckin.user_id == user_id).first()

    def get_by_date(self, user_id: int, checkin_date: date):
        return self.db.query(DailyCheckin).filter(DailyCheckin.user_id == user_id, DailyCheckin.checkin_date == checkin_date).first()

    def list(self, user_id: int, from_date: Optional[date], to_date: Optional[date], limit: int = 366, offset: int = 0):
        query = self.db.query(DailyCheckin).filter(DailyCheckin.user_id == user_id)
        if from_date:
            query = query.filter(DailyCheckin.checkin_date >= from_date)
        if to_date:
            query = query.filter(DailyCheckin.checkin_date <= to_date)
        return query.order_by(DailyCheckin.checkin_date.desc()).offset(offset).limit(limit).all()

    def update(self, checkin: DailyCheckin, data: dict):
        try:
            for field, value in data.items():
                setattr(checkin, field, value)
            self.db.commit()
            self.db.refresh(checkin)
            return checkin
        except Exception:
            self.db.rollback()
            raise
