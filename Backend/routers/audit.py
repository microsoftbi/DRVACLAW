from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from Backend.dao.audit_log_dao import AuditLogDAO
from Backend.routers._errors import http_error

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("/", response_model=List[Dict])
def get_all_audit_logs(page: Optional[int] = Query(None, ge=1),
                       page_size: Optional[int] = Query(None, ge=1, le=200)):
    try:
        limit = page_size
        offset = ((page or 1) - 1) * page_size if page_size else 0
        return AuditLogDAO.get_all(limit=limit, offset=offset)
    except Exception as e:
        raise http_error(e)


@router.get("/student/{student_id}", response_model=List[Dict])
def get_audit_logs_by_student(student_id: int):
    try:
        logs = AuditLogDAO.get_by_student_id(student_id)
        if not logs:
            raise HTTPException(status_code=404, detail="没有找到该学员的操作记录")
        return logs
    except Exception as e:
        raise http_error(e)


@router.get("/coach/{coach_id}", response_model=List[Dict])
def get_audit_logs_by_coach(coach_id: int):
    try:
        logs = AuditLogDAO.get_by_coach_id(coach_id)
        if not logs:
            raise HTTPException(status_code=404, detail="没有找到该教练的操作记录")
        return logs
    except Exception as e:
        raise http_error(e)
