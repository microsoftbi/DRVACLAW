from pydantic import BaseModel
from typing import Optional

class AppointmentBase(BaseModel):
    student_id: int
    coach_id: int
    appointment_date: str
    start_time: int
    end_time: int
    status: str

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    student_id: Optional[int] = None
    coach_id: Optional[int] = None
    appointment_date: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    status: Optional[str] = None

class Appointment(AppointmentBase):
    appointment_id: int
    create_time: str
    
    class Config:
        from_attributes = True
