from datetime import date
from fastapi import Depends, HTTPException
from app.body_metrics.repository import BodyMetricRepository

class BodyMetricService():
    def __init__(self, repository: BodyMetricRepository = Depends()):
        self.repository = repository

    def log(self, user_id: int, data):
        return self.repository.upsert(user_id, data.model_dump())

    def list(self, user_id: int, from_date, to_date, limit: int):
        return self.repository.list(user_id, from_date, to_date, limit)

    def delete(self, user_id: int, log_date: date):
        metric = self.repository.get_by_date(user_id, log_date)
        if not metric:
            raise HTTPException(status_code=404, detail="No body metric logged for this date")
        self.repository.delete(metric)
