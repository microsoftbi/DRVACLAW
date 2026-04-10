from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from Backend.schemas.recharge import Recharge, RechargeCreate, RechargeUpdate
from Backend.dao.recharge_dao import RechargeDAO

router = APIRouter(prefix="/api/recharges", tags=["充值管理"])

@router.post("", response_model=Recharge)
def create_recharge(recharge: RechargeCreate):
    try:
        recharge_id = RechargeDAO.create(
            recharge.student_id,
            recharge.amount,
            recharge.course_count,
            recharge.recharge_time
        )
        return RechargeDAO.get_by_id(recharge_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[Recharge])
def get_recharges():
    try:
        return RechargeDAO.get_all()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/student/{student_id}", response_model=List[Recharge])
def get_recharges_by_student(student_id: int):
    try:
        return RechargeDAO.get_by_student_id(student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{recharge_id}", response_model=Recharge)
def get_recharge(recharge_id: int):
    try:
        recharge = RechargeDAO.get_by_id(recharge_id)
        if not recharge:
            raise HTTPException(status_code=404, detail="充值记录不存在")
        return recharge
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{recharge_id}", response_model=Recharge)
def update_recharge(recharge_id: int, recharge: RechargeUpdate):
    try:
        success = RechargeDAO.update(
            recharge_id,
            recharge.student_id,
            recharge.amount,
            recharge.course_count,
            recharge.recharge_time
        )
        if not success:
            raise HTTPException(status_code=404, detail="充值记录不存在")
        return RechargeDAO.get_by_id(recharge_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{recharge_id}")
def delete_recharge(recharge_id: int):
    try:
        success = RechargeDAO.delete(recharge_id)
        if not success:
            raise HTTPException(status_code=404, detail="充值记录不存在")
        return {"message": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))