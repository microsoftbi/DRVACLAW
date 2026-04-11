from fastapi import APIRouter, HTTPException
from typing import List, Dict
from Backend.dao.audit_log_dao import AuditLogDAO

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])

@router.get("/", response_model=List[Dict])
def get_all_audit_logs():
    return AuditLogDAO.get_all()

@router.get("/student/{student_id}", response_model=List[Dict])
def get_audit_logs_by_student(student_id: int):
    logs = AuditLogDAO.get_by_student_id(student_id)
    if not logs:
        raise HTTPException(status_code=404, detail="没有找到该学员的操作记录")
    return logs

@router.get("/coach/{coach_id}", response_model=List[Dict])
def get_audit_logs_by_coach(coach_id: int):
    logs = AuditLogDAO.get_by_coach_id(coach_id)
    if not logs:
        raise HTTPException(status_code=404, detail="没有找到该教练的操作记录")
    return logs
