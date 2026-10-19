from datetime import date
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.analysis.models.daily_analysis import DailyAnalysis

class AnalysisRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_by_date(self, user_id: int, analysis_date: date):
        return self.db.query(DailyAnalysis).filter(DailyAnalysis.user_id == user_id, DailyAnalysis.analysis_date == analysis_date).first()

    def upsert(self, user_id: int, analysis_date: date, data: dict):
        try:
            analysis = self.get_by_date(user_id, analysis_date)
            if analysis:
                for field, value in data.items():
                    setattr(analysis, field, value)
            else:
                analysis = DailyAnalysis(user_id=user_id, analysis_date=analysis_date, **data)
                self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            return analysis
        except Exception:
            self.db.rollback()
            raise
