from pydantic import BaseModel
from typing import Optional

class AreaBase(BaseModel):
    name: str

class AreaCreate(AreaBase):
    pass

class Area(AreaBase):
    area_id: int
    
    class Config:
        from_attributes = True
