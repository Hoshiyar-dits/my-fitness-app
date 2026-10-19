from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.auth.dependencies import get_current_user
from app.activities.dto.ActivityEnums import ActivityType
from app.activities.dto.ActivityResponse import ActivityResponse
from app.activities.dto.CreateActivity import CreateActivity
from app.activities.service import ActivityService

router = APIRouter(prefix="/activities", tags=['activities'])

@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def log_activity(data: CreateActivity, current_user = Depends(get_current_user), service: ActivityService = Depends()):
    return service.create(current_user.id, data)

@router.get("/history", response_model=List[ActivityResponse])
def activity_history(
    activity_type: Optional[ActivityType] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user = Depends(get_current_user),
    service: ActivityService = Depends(),
):
    return service.history(current_user.id, activity_type.value if activity_type else None, from_date, to_date, limit, offset)
