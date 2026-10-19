from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.auth.dependencies import get_current_user
from app.checkins.dto.CheckinResponse import CheckinResponse
from app.checkins.dto.CreateCheckin import CreateCheckin
from app.checkins.dto.UpdateCheckin import UpdateCheckin
from app.checkins.service import CheckinService

router = APIRouter(prefix="/checkins", tags=['checkins'])

@router.post("", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
def create_checkin(data: CreateCheckin, current_user = Depends(get_current_user), service: CheckinService = Depends()):
    return service.create(current_user.id, data)

@router.get("/today", response_model=CheckinResponse)
def today_checkin(current_user = Depends(get_current_user), service: CheckinService = Depends()):
    return service.today(current_user.id)

@router.get("/history", response_model=List[CheckinResponse])
def checkin_history(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=30, ge=1, le=366),
    offset: int = Query(default=0, ge=0),
    current_user = Depends(get_current_user),
    service: CheckinService = Depends(),
):
    return service.history(current_user.id, from_date, to_date, limit, offset)

@router.get("/{checkin_id}", response_model=CheckinResponse)
def get_checkin(checkin_id: int, current_user = Depends(get_current_user), service: CheckinService = Depends()):
    return service.get(current_user.id, checkin_id)

@router.patch("/{checkin_id}", response_model=CheckinResponse)
def update_checkin(checkin_id: int, data: UpdateCheckin, current_user = Depends(get_current_user), service: CheckinService = Depends()):
    return service.update(current_user.id, checkin_id, data)
