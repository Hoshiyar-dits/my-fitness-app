from fastapi import Depends, HTTPException
from app.workouts.repository import WorkoutRepository

NOT_NULL_FIELDS = ("workout_date", "workout_type", "name", "duration_minutes")

class WorkoutService():
    def __init__(self, repository: WorkoutRepository = Depends()):
        self.repository = repository

    def create(self, user_id: int, data):
        return self.repository.create(user_id, data.model_dump())

    def get(self, user_id: int, workout_id: int):
        workout = self.repository.get(user_id, workout_id)
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")
        return workout

    def list(self, user_id: int, from_date, to_date, limit: int, offset: int):
        return self.repository.list(user_id, from_date, to_date, limit, offset)

    def update(self, user_id: int, workout_id: int, data):
        workout = self.get(user_id, workout_id)
        changes = data.model_dump(exclude_unset=True)
        for field in NOT_NULL_FIELDS:
            if field in changes and changes[field] is None:
                raise HTTPException(status_code=422, detail=f"{field} cannot be null")
        return self.repository.update(workout, changes)

    def delete(self, user_id: int, workout_id: int):
        self.repository.delete(self.get(user_id, workout_id))
