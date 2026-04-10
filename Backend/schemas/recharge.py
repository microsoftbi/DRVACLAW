from pydantic import BaseModel, Field
from typing import Optional

class RechargeBase(BaseModel):
    student_id: int = Field(..., description="学员ID")
    amount: float = Field(..., gt=0, description="充值金额")
    course_count: int = Field(..., gt=0, description="课程数量")
    recharge_time: str = Field(..., description="充值时间")

class RechargeCreate(RechargeBase):
    pass

class RechargeUpdate(RechargeBase):
    pass

class Recharge(RechargeBase):
    recharge_id: int
    
    class Config:
        from_attributes = True