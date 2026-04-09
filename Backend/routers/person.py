from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from Backend.schemas.person import Person, PersonCreate, PersonUpdate
from Backend.dao.person_dao import PersonDAO

router = APIRouter(prefix="/api/persons", tags=["人员管理"])

@router.post("", response_model=Person)
def create_person(person: PersonCreate):
    try:
        register_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        person_id = PersonDAO.create(
            person.name,
            person.phone,
            register_time,
            person.area_id,
            person.type
        )
        return PersonDAO.get_by_id(person_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[Person])
def get_all_persons():
    return PersonDAO.get_all()

@router.get("/students", response_model=List[Person])
def get_students():
    return PersonDAO.get_students()

@router.get("/coaches", response_model=List[Person])
def get_coaches():
    return PersonDAO.get_coaches()

@router.get("/{person_id}", response_model=Person)
def get_person(person_id: int):
    person = PersonDAO.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="人员不存在")
    return person

@router.put("/{person_id}", response_model=Person)
def update_person(person_id: int, person: PersonUpdate):
    if not PersonDAO.get_by_id(person_id):
        raise HTTPException(status_code=404, detail="人员不存在")
    PersonDAO.update(
        person_id,
        person.name,
        person.phone,
        person.area_id
    )
    return PersonDAO.get_by_id(person_id)

@router.delete("/{person_id}")
def delete_person(person_id: int):
    if not PersonDAO.get_by_id(person_id):
        raise HTTPException(status_code=404, detail="人员不存在")
    PersonDAO.delete(person_id)
    return {"message": "删除成功"}
