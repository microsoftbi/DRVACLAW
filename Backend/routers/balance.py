from fastapi import APIRouter, HTTPException
from typing import List
from Backend.dao.balance_record_dao import BalanceRecordDAO

router = APIRouter(prefix="/api/balance-records", tags=["余额记录"])

@router.get("", response_model=List[dict])
def get_all_balance_records():
    try:
        return BalanceRecordDAO.get_all()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/student/{student_id}", response_model=List[dict])
def get_balance_records_by_student(student_id: int):
    try:
        return BalanceRecordDAO.get_by_student_id(student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{record_id}", response_model=dict)
def get_balance_record(record_id: int):
    try:
        record = BalanceRecordDAO.get_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="余额记录不存在")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))