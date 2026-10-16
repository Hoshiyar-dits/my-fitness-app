from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class BodyMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    log_date: date
    weight_kg: Decimal
    body_fat_pct: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
