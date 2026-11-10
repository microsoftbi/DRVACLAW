from pydantic import BaseModel, Field
from typing import List, Optional

PHONE_PATTERN = r"^\d{11}$"

class CoachBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., pattern=PHONE_PATTERN, description="11 位手机号")
    area_id: Optional[int] = None

class CoachCreate(CoachBase):
    vehicle_ids: List[int] = []

class CoachUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, pattern=PHONE_PATTERN)
    area_id: Optional[int] = None
    vehicle_ids: Optional[List[int]] = None

class Coach(CoachBase):
    coach_id: int
    register_time: str
    vehicle_ids: List[int] = []

    class Config:
        from_attributes = True
