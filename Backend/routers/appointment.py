from fastapi import APIRouter, HTTPException
from typing import List
from Backend.schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate
from Backend.dao.appointment_dao import AppointmentDAO

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
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[Appointment])
def get_all_appointments():
    return AppointmentDAO.get_all()

@router.get("/{appointment_id}", response_model=Appointment)
def get_appointment(appointment_id: int):
    appointment = AppointmentDAO.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    return appointment

@router.get("/student/{student_id}", response_model=List[Appointment])
def get_appointments_by_student(student_id: int):
    return AppointmentDAO.get_by_student_id(student_id)

@router.get("/coach/{coach_id}", response_model=List[Appointment])
def get_appointments_by_coach(coach_id: int):
    return AppointmentDAO.get_by_coach_id(coach_id)

@router.get("/date/{appointment_date}", response_model=List[Appointment])
def get_appointments_by_date(appointment_date: str):
    return AppointmentDAO.get_by_date(appointment_date)

@router.put("/{appointment_id}", response_model=Appointment)
def update_appointment(appointment_id: int, appointment: AppointmentUpdate):
    if not AppointmentDAO.get_by_id(appointment_id):
        raise HTTPException(status_code=404, detail="预约不存在")
    AppointmentDAO.update(
        appointment_id,
        appointment.student_id,
        appointment.coach_id,
        appointment.appointment_date,
        appointment.start_time,
        appointment.end_time,
        appointment.status
    )
    return AppointmentDAO.get_by_id(appointment_id)

@router.delete("/{appointment_id}")
def delete_appointment(appointment_id: int):
    if not AppointmentDAO.get_by_id(appointment_id):
        raise HTTPException(status_code=404, detail="预约不存在")
    AppointmentDAO.delete(appointment_id)
    return {"message": "删除成功"}
