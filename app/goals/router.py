from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.auth.dependencies import get_current_user
from app.goals.dto.CreateGoal import CreateGoal
from app.goals.dto.UpdateGoal import UpdateGoal
from app.goals.dto.GoalResponse import GoalResponse
from app.goals.dto.GoalEnums import GoalStatus
from app.goals.service import GoalService

router = APIRouter(prefix="/goals", tags=['goals'])

@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(data: CreateGoal, current_user = Depends(get_current_user), service: GoalService = Depends()):
    return service.create(current_user.id, data)

@router.get("", response_model=List[GoalResponse])
def list_goals(
    status: Optional[GoalStatus] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user = Depends(get_current_user),
    service: GoalService = Depends(),
):
    return service.list(current_user.id, status.value if status else None, limit, offset)

@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: int, current_user = Depends(get_current_user), service: GoalService = Depends()):
    return service.get(current_user.id, goal_id)

@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: int, data: UpdateGoal, current_user = Depends(get_current_user), service: GoalService = Depends()):
    return service.update(current_user.id, goal_id, data)
