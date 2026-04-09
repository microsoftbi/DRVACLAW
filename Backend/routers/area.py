from fastapi import APIRouter, HTTPException
from typing import List
from Backend.schemas.area import Area, AreaCreate
from Backend.dao.area_dao import AreaDAO

router = APIRouter(prefix="/api/areas", tags=["区域管理"])

@router.post("", response_model=Area)
def create_area(area: AreaCreate):
    try:
        area_id = AreaDAO.create(area.name)
        return AreaDAO.get_by_id(area_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[Area])
def get_all_areas():
    return AreaDAO.get_all()

@router.get("/{area_id}", response_model=Area)
def get_area(area_id: int):
    area = AreaDAO.get_by_id(area_id)
    if not area:
        raise HTTPException(status_code=404, detail="区域不存在")
    return area

@router.put("/{area_id}", response_model=Area)
def update_area(area_id: int, area: AreaCreate):
    if not AreaDAO.get_by_id(area_id):
        raise HTTPException(status_code=404, detail="区域不存在")
    AreaDAO.update(area_id, area.name)
    return AreaDAO.get_by_id(area_id)

@router.delete("/{area_id}")
def delete_area(area_id: int):
    if not AreaDAO.get_by_id(area_id):
        raise HTTPException(status_code=404, detail="区域不存在")
    AreaDAO.delete(area_id)
    return {"message": "删除成功"}
