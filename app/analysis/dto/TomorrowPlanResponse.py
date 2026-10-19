from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from app.analysis.dto.DailyAnalysisResponse import DailyAnalysisResponse
from app.training.dto.PlanResponse import PlanResponse

class TomorrowPlanResponse(BaseModel):
    date: date
    decision: str
    reasons: List[str]
    safety_message: Optional[str]
    message: str
    requires_confirmation: bool
    scheduled_plans: List[PlanResponse]
    proposed_plans: List[PlanResponse]
    analysis: DailyAnalysisResponse
