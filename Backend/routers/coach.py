from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from datetime import datetime
from Backend.schemas.coach import Coach, CoachCreate, CoachUpdate
from Backend.schemas.vehicle import Vehicle
from Backend.dao.coach_dao import CoachDAO
from Backend.routers._errors import http_error

router = APIRouter(prefix="/api/coaches", tags=["教练管理"])


def _with_vehicles(coach: Dict) -> Dict:
    coach['vehicle_ids'] = CoachDAO.get_vehicle_ids(coach['coach_id'])
    return coach


@router.post("", response_model=Coach)
def create_coach(coach: CoachCreate):
    try:
        register_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        coach_id = CoachDAO.create(
            coach.name,
            coach.phone,
            register_time,
            coach.area_id,
            coach.vehicle_ids
        )
        return _with_vehicles(CoachDAO.get_by_id(coach_id))
    except Exception as e:
        raise http_error(e)


@router.get("", response_model=List[Coach])
def get_all_coaches(page: Optional[int] = Query(None, ge=1),
                    page_size: Optional[int] = Query(None, ge=1, le=200)):
    try:
        limit = page_size
        offset = ((page or 1) - 1) * page_size if page_size else 0
        return CoachDAO.get_all_with_vehicles(limit=limit, offset=offset)
    except Exception as e:
        raise http_error(e)


@router.get("/{coach_id}", response_model=Coach)
def get_coach(coach_id: int):
    try:
        coach = CoachDAO.get_by_id(coach_id)
        if not coach:
            raise HTTPException(status_code=404, detail="教练不存在")
        return _with_vehicles(coach)
    except Exception as e:
        raise http_error(e)


@router.get("/{coach_id}/vehicles", response_model=List[Vehicle])
def get_coach_vehicles(coach_id: int):
    try:
        if not CoachDAO.get_by_id(coach_id):
            raise HTTPException(status_code=404, detail="教练不存在")
        return CoachDAO.get_vehicles(coach_id)
    except Exception as e:
        raise http_error(e)


@router.put("/{coach_id}", response_model=Coach)
def update_coach(coach_id: int, coach: CoachUpdate):
    try:
        if not CoachDAO.get_by_id(coach_id):
            raise HTTPException(status_code=404, detail="教练不存在")
        CoachDAO.update(
            coach_id,
            coach.name,
            coach.phone,
            coach.area_id
        )
        if coach.vehicle_ids is not None:
            CoachDAO.set_vehicles(coach_id, coach.vehicle_ids)
        return _with_vehicles(CoachDAO.get_by_id(coach_id))
    except Exception as e:
        raise http_error(e)


@router.delete("/{coach_id}")
def delete_coach(coach_id: int):
    try:
        if not CoachDAO.delete(coach_id):
            raise HTTPException(status_code=404, detail="教练不存在")
        return {"message": "删除成功"}
    except Exception as e:
        raise http_error(e)
