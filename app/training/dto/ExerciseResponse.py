from typing import Optional
from pydantic import BaseModel, ConfigDict

class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    description: Optional[str]
    is_high_impact: bool
    required_equipment: Optional[str]
