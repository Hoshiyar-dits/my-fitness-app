from datetime import date
from typing import Optional
from fastapi import Depends, HTTPException
from app.body_metrics.repository import BodyMetricRepository
from app.checkins.repository import CheckinRepository
from app.goals.service import GoalService

BODY_FIELDS = ("weight_kg", "body_fat_pct", "body_fat_method")

class CheckinService():
    def __init__(self, repository: CheckinRepository = Depends(), body_metrics: BodyMetricRepository = Depends(), goals: GoalService = Depends()):
        self.repository = repository
        self.body_metrics = body_metrics
        self.goals = goals

    def create(self, user_id: int, data):
        values = data.model_dump()
        if self.repository.get_by_date(user_id, values["checkin_date"]):
            raise HTTPException(status_code=409, detail="A check-in already exists for this date. Update it instead.")
        body = {field: values.pop(field) for field in BODY_FIELDS}
        self._check_body_metric(user_id, values["checkin_date"], body)
        checkin = self.repository.create(user_id, values)
        self._save_body_metric(user_id, checkin.checkin_date, body)
        return self._with_body_metric(checkin)

    def get(self, user_id: int, checkin_id: int):
        checkin = self.repository.get(user_id, checkin_id)
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
        return self._with_body_metric(checkin)

    def today(self, user_id: int):
        checkin = self.repository.get_by_date(user_id, date.today())
        if not checkin:
            raise HTTPException(status_code=404, detail="No check-in recorded today")
        return self._with_body_metric(checkin)

    def by_date(self, user_id: int, day: date):
        checkin = self.repository.get_by_date(user_id, day)
        return self._with_body_metric(checkin) if checkin else None

    def history(self, user_id: int, from_date: Optional[date], to_date: Optional[date], limit: int, offset: int):
        if from_date and to_date and to_date < from_date:
            raise HTTPException(status_code=422, detail="to_date must be on or after from_date")
        return [self._with_body_metric(c) for c in self.repository.list(user_id, from_date, to_date, limit, offset)]

    def update(self, user_id: int, checkin_id: int, data):
        checkin = self.repository.get(user_id, checkin_id)
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
        changes = data.model_dump(exclude_unset=True)
        if "warning_symptoms" in changes and changes["warning_symptoms"] is None:
            changes["warning_symptoms"] = []
        body = {field: changes.pop(field) for field in BODY_FIELDS if field in changes}
        self._check_body_metric(user_id, checkin.checkin_date, body)
        checkin = self.repository.update(checkin, changes)
        self._save_body_metric(user_id, checkin.checkin_date, body)
        return self._with_body_metric(checkin)

    def _check_body_metric(self, user_id: int, day: date, body: dict):
        if body.get("body_fat_pct") is not None and body.get("weight_kg") is None and not self.body_metrics.get_by_date(user_id, day):
            raise HTTPException(status_code=422, detail="body_fat_pct is stored with that day's weigh-in, so include weight_kg")

    def _save_body_metric(self, user_id: int, day: date, body: dict):
        body = {k: v for k, v in body.items() if v is not None}
        if not body:
            return
        existing = self.body_metrics.get_by_date(user_id, day)
        if "weight_kg" not in body and existing is None:
            return
        metric = self.body_metrics.upsert(user_id, {"log_date": day, **body})
        self.goals.record_measurement(user_id, "body_weight", metric.weight_kg, day)
        if metric.body_fat_pct is not None:
            self.goals.record_measurement(user_id, "body_fat", metric.body_fat_pct, day)

    def _with_body_metric(self, checkin):
        checkin.body_metric = self.body_metrics.get_by_date(checkin.user_id, checkin.checkin_date)
        return checkin
