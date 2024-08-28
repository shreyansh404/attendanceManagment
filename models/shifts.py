from pydantic import BaseModel
from typing import Optional
from enum import Enum
import time

class ShiftName(str, Enum):
    MORNING = "morning"
    EVENING = "evening"
    AFTERNOON = "afternoon"
    NIGHT = "night"

class Shifts(BaseModel):
    shift_name: ShiftName
    start_time: str
    end_time: str
    created_at: Optional[str] = int(time.time())
    updated_at: Optional[str] = int(time.time())
    user_id: Optional[str] = None