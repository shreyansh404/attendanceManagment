from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import time

class Attendance(BaseModel):
    user_id: str
    date: str
    time_in: str
    image: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None