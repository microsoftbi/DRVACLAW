from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from Backend.schemas.student import Student, StudentCreate, StudentUpdate
from Backend.dao.student_dao import StudentDAO
from Backend.routers._errors import http_error

router = APIRouter(prefix="/api/students", tags=["学员管理"])


@router.post("", response_model=Student)
def create_student(student: StudentCreate):
    try:
        register_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        student_id = StudentDAO.create(
            student.name,
            student.phone,
            register_time,
            student.area_id,
            student.driving_years,
            student.remark
        )
        return StudentDAO.get_by_id(student_id)
    except Exception as e:
        raise http_error(e)


@router.get("", response_model=List[Student])
def get_all_students(page: Optional[int] = Query(None, ge=1),
                     page_size: Optional[int] = Query(None, ge=1, le=200)):
    try:
        limit = page_size
        offset = ((page or 1) - 1) * page_size if page_size else 0
        return StudentDAO.get_all(limit=limit, offset=offset)
    except Exception as e:
        raise http_error(e)


@router.get("/{student_id}", response_model=Student)
def get_student(student_id: int):
    try:
        student = StudentDAO.get_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="学员不存在")
        return student
    except Exception as e:
        raise http_error(e)


@router.put("/{student_id}", response_model=Student)
def update_student(student_id: int, student: StudentUpdate):
    try:
        if not StudentDAO.get_by_id(student_id):
            raise HTTPException(status_code=404, detail="学员不存在")
        StudentDAO.update(
            student_id,
            student.name,
            student.phone,
            student.area_id,
            student.driving_years,
            student.remark
        )
        return StudentDAO.get_by_id(student_id)
    except Exception as e:
        raise http_error(e)


@router.delete("/{student_id}")
def delete_student(student_id: int):
    try:
        if not StudentDAO.delete(student_id):
            raise HTTPException(status_code=404, detail="学员不存在")
        return {"message": "删除成功"}
    except Exception as e:
        raise http_error(e)
