from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from Backend.schemas.vehicle import Vehicle, VehicleCreate, VehicleUpdate
from Backend.dao.vehicle_dao import VehicleDAO
from Backend.routers._errors import http_error

router = APIRouter(prefix="/api/vehicles", tags=["车辆管理"])


@router.post("", response_model=Vehicle)
def create_vehicle(vehicle: VehicleCreate):
    try:
        create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        vehicle_id = VehicleDAO.create(
            vehicle.vehicle_type,
            vehicle.brand,
            vehicle.model,
            create_time
        )
        return VehicleDAO.get_by_id(vehicle_id)
    except Exception as e:
        raise http_error(e)


@router.get("", response_model=List[Vehicle])
def get_all_vehicles(page: Optional[int] = Query(None, ge=1),
                     page_size: Optional[int] = Query(None, ge=1, le=200)):
    try:
        limit = page_size
        offset = ((page or 1) - 1) * page_size if page_size else 0
        return VehicleDAO.get_all(limit=limit, offset=offset)
    except Exception as e:
        raise http_error(e)


@router.get("/{vehicle_id}", response_model=Vehicle)
def get_vehicle(vehicle_id: int):
    try:
        vehicle = VehicleDAO.get_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="车辆不存在")
        return vehicle
    except Exception as e:
        raise http_error(e)


@router.put("/{vehicle_id}", response_model=Vehicle)
def update_vehicle(vehicle_id: int, vehicle: VehicleUpdate):
    try:
        if not VehicleDAO.get_by_id(vehicle_id):
            raise HTTPException(status_code=404, detail="车辆不存在")
        VehicleDAO.update(
            vehicle_id,
            vehicle.vehicle_type,
            vehicle.brand,
            vehicle.model
        )
        return VehicleDAO.get_by_id(vehicle_id)
    except Exception as e:
        raise http_error(e)


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int):
    try:
        if not VehicleDAO.delete(vehicle_id):
            raise HTTPException(status_code=404, detail="车辆不存在")
        return {"message": "删除成功"}
    except Exception as e:
        raise http_error(e)
