from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_date: date
    end_date: date
    status: str
    experience_level: str
    training_background: Optional[str]
    available_minutes_per_day: int
    equipment: List[str]
    injury_history: Optional[str]
    current_pain: Optional[str]
    medical_restrictions: Optional[str]
    medical_clearance_confirmed: bool
    assessment_run_distance_m: Decimal
    assessment_sprint_distance_m: Decimal
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class ProgramCreated(BaseModel):
    program: ProgramResponse
    sessions_created: int
    goals_created: int
    safety_message: Optional[str] = None
    missing_information: List[str] = []
