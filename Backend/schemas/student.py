from pydantic import BaseModel, Field
from typing import Optional

# 手机号统一为 11 位数字，避免脏数据进入业务表
PHONE_PATTERN = r"^\d{11}$"


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., pattern=PHONE_PATTERN, description="11 位手机号")
    area_id: Optional[int] = None
    driving_years: Optional[int] = Field(0, ge=0, le=60)
    remark: Optional[str] = None

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, pattern=PHONE_PATTERN)
    area_id: Optional[int] = None
    driving_years: Optional[int] = Field(None, ge=0, le=60)
    remark: Optional[str] = None

class Student(StudentBase):
    student_id: int
    register_time: str

    class Config:
        from_attributes = True
