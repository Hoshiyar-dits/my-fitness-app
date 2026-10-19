from datetime import date
from typing import Optional
from fastapi import Depends, HTTPException
from app.activities.repository import ActivityRepository
from app.goals.dto.GoalEnums import ACTIVITY_GOAL_TYPES
from app.goals.service import GoalService
from app.training.repository import PlanRepository

class ActivityService():
    def __init__(self, repository: ActivityRepository = Depends(), plans: PlanRepository = Depends(), goals: GoalService = Depends()):
        self.repository = repository
        self.plans = plans
        self.goals = goals

    def create(self, user_id: int, data, planned_workout_id: Optional[int] = None):
        values = data.model_dump(exclude={"splits"})
        if planned_workout_id is not None:
            values["planned_workout_id"] = planned_workout_id
        if values["planned_workout_id"] is not None and not self.plans.get(user_id, values["planned_workout_id"]):
            raise HTTPException(status_code=404, detail="Planned workout not found")
        splits = [s.model_dump() for s in data.splits]
        activity = self.repository.create(user_id, values, splits)

        value = activity.elapsed_seconds if activity.activity_type in ("run", "sprint") else activity.jump_cm
        self.goals.record_measurement(
            user_id, ACTIVITY_GOAL_TYPES[activity.activity_type].value, value, activity.activity_date,
            distance_m=activity.distance_m, technique=activity.technique,
        )
        return activity

    def history(self, user_id: int, activity_type: Optional[str], from_date: Optional[date], to_date: Optional[date], limit: int, offset: int):
        if from_date and to_date and to_date < from_date:
            raise HTTPException(status_code=422, detail="to_date must be on or after from_date")
        return self.repository.list(user_id, [activity_type] if activity_type else None, from_date, to_date, limit, offset)
