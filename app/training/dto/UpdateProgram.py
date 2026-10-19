from typing import Literal, Optional
from pydantic import BaseModel

class UpdateProgram(BaseModel):
    status: Optional[Literal["cancelled"]] = None
    medical_clearance_confirmed: Optional[Literal[True]] = None
