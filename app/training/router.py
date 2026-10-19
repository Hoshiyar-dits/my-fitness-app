from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.auth.dependencies import get_current_user
from app.analysis.dto.TomorrowPlanResponse import TomorrowPlanResponse
from app.analysis.service import AnalysisService
from app.training.dto.CompletePlan import CompletePlan, SkipPlan
from app.training.dto.CreatePlan import CreatePlan
from app.training.dto.CreateProgram import CreateProgram
from app.training.dto.ExerciseResponse import ExerciseResponse
from app.training.dto.PlanResponse import PlanResponse
from app.training.dto.ProgramResponse import ProgramCreated, ProgramResponse
from app.training.dto.TrainingEnums import PlanStatus
from app.training.dto.UpdatePlan import UpdatePlan
from app.training.dto.UpdateProgram import UpdateProgram
from app.training.repository import ExerciseRepository
from app.training.service import PlanService, ProgramService

router = APIRouter(tags=['training'])

@router.get("/exercises", response_model=List[ExerciseResponse])
def list_exercises(category: Optional[str] = None, current_user = Depends(get_current_user), repository: ExerciseRepository = Depends()):
    return repository.list(category)

@router.post("/programs", response_model=ProgramCreated, status_code=status.HTTP_201_CREATED)
def create_program(data: CreateProgram, current_user = Depends(get_current_user), service: ProgramService = Depends()):
    """Initial assessment: records baseline data and creates the 25-day calendar (unless medical clearance is needed first)."""
    return service.create(current_user.id, data)

@router.get("/programs/current", response_model=ProgramResponse)
def current_program(current_user = Depends(get_current_user), service: ProgramService = Depends()):
    return service.current(current_user.id)

@router.get("/programs/{program_id}", response_model=ProgramResponse)
def get_program(program_id: int, current_user = Depends(get_current_user), service: ProgramService = Depends()):
    return service.get(current_user.id, program_id)

@router.patch("/programs/{program_id}", response_model=ProgramResponse)
def update_program(program_id: int, data: UpdateProgram, current_user = Depends(get_current_user), service: ProgramService = Depends()):
    """Cancel the program, or confirm medical clearance (which generates the calendar)."""
    return service.update(current_user.id, program_id, data)

@router.get("/plans/today", response_model=List[PlanResponse])
def plans_today(current_user = Depends(get_current_user), service: PlanService = Depends()):
    return service.today(current_user.id)

@router.post("/plans/tomorrow", response_model=TomorrowPlanResponse)
def plan_tomorrow(current_user = Depends(get_current_user), service: AnalysisService = Depends()):
    """Reviews today and proposes an adjusted plan for tomorrow if needed. Proposals must be confirmed via PATCH /plans/{id}."""
    return service.propose_tomorrow(current_user.id, date.today(), source="rules")

@router.get("/plans", response_model=List[PlanResponse])
def list_plans(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    status: Optional[PlanStatus] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user = Depends(get_current_user),
    service: PlanService = Depends(),
):
    return service.list(current_user.id, from_date, to_date, status.value if status else None, limit, offset)

@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(data: CreatePlan, current_user = Depends(get_current_user), service: PlanService = Depends()):
    return service.create(current_user.id, data)

@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, current_user = Depends(get_current_user), service: PlanService = Depends()):
    return service.get(current_user.id, plan_id)

@router.patch("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: int, data: UpdatePlan, current_user = Depends(get_current_user), service: PlanService = Depends()):
    return service.update(current_user.id, plan_id, data)

@router.post("/plans/{plan_id}/complete", response_model=PlanResponse)
def complete_plan(plan_id: int, data: CompletePlan, current_user = Depends(get_current_user), service: PlanService = Depends()):
    return service.complete(current_user.id, plan_id, data)

@router.post("/plans/{plan_id}/skip", response_model=PlanResponse)
def skip_plan(plan_id: int, data: SkipPlan, current_user = Depends(get_current_user), service: PlanService = Depends()):
    return service.skip(current_user.id, plan_id, data.reason)
