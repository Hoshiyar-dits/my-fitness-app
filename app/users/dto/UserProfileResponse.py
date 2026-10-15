from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, computed_field

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date_of_birth: date
    height_cm: Decimal
    gender: Optional[str]
    activity_level: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
