from fastapi import APIRouter, HTTPException
from typing import List
from Backend.schemas.area import Area, AreaCreate
from Backend.dao.area_dao import AreaDAO
from Backend.routers._errors import http_error

router = APIRouter(prefix="/api/areas", tags=["区域管理"])


@router.post("", response_model=Area)
def create_area(area: AreaCreate):
    try:
        area_id = AreaDAO.create(area.name)
        return AreaDAO.get_by_id(area_id)
    except Exception as e:
        raise http_error(e)


@router.get("", response_model=List[Area])
def get_all_areas():
    try:
        return AreaDAO.get_all()
    except Exception as e:
        raise http_error(e)


@router.get("/{area_id}", response_model=Area)
def get_area(area_id: int):
    try:
        area = AreaDAO.get_by_id(area_id)
        if not area:
            raise HTTPException(status_code=404, detail="区域不存在")
        return area
    except Exception as e:
        raise http_error(e)


@router.put("/{area_id}", response_model=Area)
def update_area(area_id: int, area: AreaCreate):
    try:
        if not AreaDAO.update(area_id, area.name):
            raise HTTPException(status_code=404, detail="区域不存在")
        return AreaDAO.get_by_id(area_id)
    except Exception as e:
        raise http_error(e)


@router.delete("/{area_id}")
def delete_area(area_id: int):
    try:
        if not AreaDAO.delete(area_id):
            raise HTTPException(status_code=404, detail="区域不存在")
        return {"message": "删除成功"}
    except Exception as e:
        raise http_error(e)
