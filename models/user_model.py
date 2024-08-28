from pydantic import BaseModel, EmailStr
import time
from enum import Enum
from typing import Optional 
from datetime import datetime

class Role(str, Enum):
    STAFF = "staff"
    MANAGER = "manager"

class UserCreation(BaseModel):
    username: str
    password: str
    confirm_password: str
    role: Role
    full_name: str
    email: EmailStr
    manager_secret_key: Optional[str] = ""
    manager_id: Optional[str] = ""
    created_at: Optional[datetime] = time.time()
    updated_at: Optional[datetime] = time.time()   

class UserLogin(BaseModel):
    email: EmailStr
    password: str
