from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from Backend.dao.balance_record_dao import BalanceRecordDAO
from Backend.routers._errors import http_error

router = APIRouter(prefix="/api/balance-records", tags=["余额记录"])


@router.get("", response_model=List[dict])
def get_all_balance_records(page: Optional[int] = Query(None, ge=1),
                            page_size: Optional[int] = Query(None, ge=1, le=200)):
    try:
        limit = page_size
        offset = ((page or 1) - 1) * page_size if page_size else 0
        return BalanceRecordDAO.get_all(limit=limit, offset=offset)
    except Exception as e:
        raise http_error(e)


@router.get("/student/{student_id}", response_model=List[dict])
def get_balance_records_by_student(student_id: int):
    try:
        return BalanceRecordDAO.get_by_student_id(student_id)
    except Exception as e:
        raise http_error(e)


@router.get("/{record_id}", response_model=dict)
def get_balance_record(record_id: int):
    try:
        record = BalanceRecordDAO.get_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="余额记录不存在")
        return record
    except Exception as e:
        raise http_error(e)
