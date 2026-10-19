from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class DailyAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_date: date
    program_id: Optional[int]
    readiness: str
    summary: str
    reasons: List[str]
    metrics: Dict[str, Any]
    source_refs: Dict[str, Any]
    recommendation: Optional[str]
    safety_message: Optional[str]
    generated_by: str
    proposed_plan_id: Optional[int]
    created_at: datetime
    updated_at: datetime
