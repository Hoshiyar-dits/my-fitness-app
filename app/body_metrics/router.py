from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.auth.dependencies import get_current_user
from app.body_metrics.dto.LogBodyMetric import LogBodyMetric
from app.body_metrics.dto.BodyMetricResponse import BodyMetricResponse
from app.body_metrics.service import BodyMetricService

router = APIRouter(prefix="/body-metrics", tags=['body-metrics'])

@router.put("", response_model=BodyMetricResponse)
def log_body_metric(data: LogBodyMetric, current_user = Depends(get_current_user), service: BodyMetricService = Depends()):
    return service.log(current_user.id, data)

@router.get("", response_model=List[BodyMetricResponse])
def list_body_metrics(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=90, ge=1, le=366),
    current_user = Depends(get_current_user),
    service: BodyMetricService = Depends(),
):
    return service.list(current_user.id, from_date, to_date, limit)

@router.delete("/{log_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_body_metric(log_date: date, current_user = Depends(get_current_user), service: BodyMetricService = Depends()):
    service.delete(current_user.id, log_date)
