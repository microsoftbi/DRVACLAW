from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from Backend.schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate
from Backend.dao.appointment_dao import AppointmentDAO
from Backend.routers._errors import http_error

router = APIRouter(prefix="/api/appointments", tags=["预约管理"])


@router.post("", response_model=Appointment)
def create_appointment(appointment: AppointmentCreate):
    try:
        appointment_id = AppointmentDAO.create(
            appointment.student_id,
            appointment.coach_id,
            appointment.appointment_date,
            appointment.start_time,
            appointment.end_time,
            appointment.status
        )
        return AppointmentDAO.get_by_id(appointment_id)
    except Exception as e:
        raise http_error(e)


@router.get("", response_model=List[Appointment])
def get_all_appointments(page: Optional[int] = Query(None, ge=1),
                         page_size: Optional[int] = Query(None, ge=1, le=200)):
    try:
        limit = page_size
        offset = ((page or 1) - 1) * page_size if page_size else 0
        return AppointmentDAO.get_all(limit=limit, offset=offset)
    except Exception as e:
        raise http_error(e)


@router.get("/student/{student_id}", response_model=List[Appointment])
def get_appointments_by_student(student_id: int):
    try:
        return AppointmentDAO.get_by_student_id(student_id)
    except Exception as e:
        raise http_error(e)


@router.get("/coach/{coach_id}", response_model=List[Appointment])
def get_appointments_by_coach(coach_id: int):
    try:
        return AppointmentDAO.get_by_coach_id(coach_id)
    except Exception as e:
        raise http_error(e)


@router.get("/date/{appointment_date}", response_model=List[Appointment])
def get_appointments_by_date(appointment_date: str):
    try:
        return AppointmentDAO.get_by_date(appointment_date)
    except Exception as e:
        raise http_error(e)


@router.get("/{appointment_id}", response_model=Appointment)
def get_appointment(appointment_id: int):
    try:
        appointment = AppointmentDAO.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="预约不存在")
        return appointment
    except Exception as e:
        raise http_error(e)


@router.put("/{appointment_id}", response_model=Appointment)
def update_appointment(appointment_id: int, appointment: AppointmentUpdate):
    try:
        success = AppointmentDAO.update(
            appointment_id,
            appointment.student_id,
            appointment.coach_id,
            appointment.appointment_date,
            appointment.start_time,
            appointment.end_time,
            appointment.status
        )
        if not success:
            raise HTTPException(status_code=404, detail="预约不存在")
        return AppointmentDAO.get_by_id(appointment_id)
    except Exception as e:
        raise http_error(e)


@router.delete("/{appointment_id}")
def delete_appointment(appointment_id: int):
    try:
        success = AppointmentDAO.delete(appointment_id)
        if not success:
            raise HTTPException(status_code=404, detail="预约不存在")
        return {"message": "删除成功"}
    except Exception as e:
        raise http_error(e)
