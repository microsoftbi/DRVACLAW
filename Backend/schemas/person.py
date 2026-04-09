from pydantic import BaseModel
from typing import Optional

class PersonBase(BaseModel):
    name: str
    phone: str
    area_id: Optional[int] = None
    type: str

class PersonCreate(PersonBase):
    pass

class PersonUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    area_id: Optional[int] = None

class Person(PersonBase):
    person_id: int
    register_time: str
    
    class Config:
        from_attributes = True
