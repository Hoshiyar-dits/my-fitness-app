from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.auth.dependencies import get_current_user
from app.workouts.dto.CreateWorkout import CreateWorkout
from app.workouts.dto.UpdateWorkout import UpdateWorkout
from app.workouts.dto.WorkoutResponse import WorkoutResponse
from app.workouts.service import WorkoutService

router = APIRouter(prefix="/workouts", tags=['workouts'])

@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create_workout(data: CreateWorkout, current_user = Depends(get_current_user), service: WorkoutService = Depends()):
    return service.create(current_user.id, data)

@router.get("", response_model=List[WorkoutResponse])
def list_workouts(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user = Depends(get_current_user),
    service: WorkoutService = Depends(),
):
    return service.list(current_user.id, from_date, to_date, limit, offset)

@router.get("/{workout_id}", response_model=WorkoutResponse)
def get_workout(workout_id: int, current_user = Depends(get_current_user), service: WorkoutService = Depends()):
    return service.get(current_user.id, workout_id)

@router.patch("/{workout_id}", response_model=WorkoutResponse)
def update_workout(workout_id: int, data: UpdateWorkout, current_user = Depends(get_current_user), service: WorkoutService = Depends()):
    return service.update(current_user.id, workout_id, data)

@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, current_user = Depends(get_current_user), service: WorkoutService = Depends()):
    service.delete(current_user.id, workout_id)
