from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import Depends, HTTPException
from app.activities.metrics import same_distance
from app.goals.dto.GoalEnums import TIMED_GOALS, JUMP_GOALS
from app.goals.repository import GoalRepository
from app.training.repository import ProgramRepository

NOT_NULL_FIELDS = ("target_date", "target_value", "status")

class GoalService():
    def __init__(self, repository: GoalRepository = Depends(), programs: ProgramRepository = Depends()):
        self.repository = repository
        self.programs = programs

    def create(self, user_id: int, data):
        values = data.model_dump()
        if values["program_id"] is not None and not self.programs.get(user_id, values["program_id"]):
            raise HTTPException(status_code=404, detail="Program not found")
        return self.repository.create(user_id, values)

    def get(self, user_id: int, goal_id: int):
        goal = self.repository.get(user_id, goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal

    def list(self, user_id: int, status: Optional[str], limit: int, offset: int):
        return self.repository.list(user_id, status, limit, offset)

    def update(self, user_id: int, goal_id: int, data):
        goal = self.get(user_id, goal_id)
        changes = data.model_dump(exclude_unset=True)
        for field in NOT_NULL_FIELDS:
            if field in changes and changes[field] is None:
                raise HTTPException(status_code=422, detail=f"{field} cannot be null")
        if changes.get("target_date") and changes["target_date"] <= goal.start_date:
            raise HTTPException(status_code=422, detail="target_date must be after start_date")
        if goal.unit == "pct" and any(changes.get(f) is not None and changes[f] >= 100 for f in ("baseline_value", "target_value", "current_value")):
            raise HTTPException(status_code=422, detail="body fat values are percentages below 100")
        if changes.get("current_value") is not None and "current_value_date" not in changes:
            changes["current_value_date"] = date.today()
        return self.repository.update(goal, changes)

    def record_measurement(self, user_id: int, goal_type: str, value, on_date: date, distance_m=None, technique: Optional[str] = None):
        """Updates current_value of matching active goals. Only comparable measurements count: timed goals
        need the same distance, jump goals the same technique (when the goal specifies one)."""
        value = Decimal(str(value))
        performance_goal = goal_type in TIMED_GOALS or goal_type in JUMP_GOALS
        for goal in self.repository.active_of_type(user_id, goal_type):
            if goal_type in TIMED_GOALS and not same_distance(goal.reference_distance_m, distance_m):
                continue
            if goal_type in JUMP_GOALS and goal.technique and goal.technique != technique:
                continue
            if goal.current_value_date and on_date < goal.current_value_date:
                continue  # an older measurement never replaces a newer one
            if performance_goal and goal.current_value_date == on_date and goal.current_value is not None:
                # several attempts on one day: keep that day's best
                better = value < goal.current_value if goal_type in TIMED_GOALS else value > goal.current_value
                if not better:
                    continue
            self.repository.update(goal, {"current_value": value, "current_value_date": on_date})
