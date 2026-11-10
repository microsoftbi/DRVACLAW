from pydantic import BaseModel
from typing import Literal, Optional

class VehicleBase(BaseModel):
    vehicle_type: Literal['SUV', '轿车']
    brand: str
    model: str

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    vehicle_type: Optional[Literal['SUV', '轿车']] = None
    brand: Optional[str] = None
    model: Optional[str] = None

class Vehicle(VehicleBase):
    vehicle_id: int
    create_time: str

    class Config:
        from_attributes = True
