"""业务系统工具集：把驾驶智陪工作台的后端 API 暴露给 deepagents。

所有工具都直接调用业务后端（默认 http://127.0.0.1:8002），返回 JSON 字符串，
便于模型阅读与二次汇总。写操作会由 Agent 层触发人工审批。
"""

import json
import os
from datetime import datetime
from typing import Optional

import requests
from langchain_core.tools import tool

API_BASE = os.environ.get("DRVACLAW_API_BASE", "http://127.0.0.1:8002").rstrip("/")
TIMEOUT = 20

APPOINTMENT_STATUS = ["待确认", "已确认", "已取消", "已完成"]
VEHICLE_TYPES = ["SUV", "轿车"]


def _request(method: str, path: str, params=None, body=None):
    try:
        resp = requests.request(method, API_BASE + path, params=params, json=body, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return {"error": f"无法连接业务后端 {API_BASE}：{exc}"}
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail")
        except ValueError:
            detail = resp.text[:300]
        return {"error": f"接口返回 {resp.status_code}：{detail}"}
    if resp.status_code == 204 or not resp.content:
        return {"ok": True}
    try:
        return resp.json()
    except ValueError:
        return {"ok": True}


def _dump(data) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _error(message: str) -> str:
    return _dump({"error": message})


def _areas() -> list:
    data = _request("GET", "/api/areas")
    return data if isinstance(data, list) else []


def _area_map() -> dict:
    return {a.get("area_id"): a.get("name") for a in _areas()}


def _students() -> list:
    data = _request("GET", "/api/students", {"page": 1, "page_size": 200})
    return data if isinstance(data, list) else []


def _coaches() -> list:
    data = _request("GET", "/api/coaches", {"page": 1, "page_size": 200})
    return data if isinstance(data, list) else []


def _vehicles() -> list:
    data = _request("GET", "/api/vehicles", {"page": 1, "page_size": 200})
    return data if isinstance(data, list) else []


def _find_area(area_name: Optional[str]):
    if not area_name:
        return None, _error("缺少区域名称 area_name。")
    for area in _areas():
        if area.get("name") == area_name.strip():
            return area, None
    names = "、".join(a.get("name", "") for a in _areas()) or "（暂无区域）"
    return None, _error(f"未找到区域「{area_name}」。现有区域：{names}")


def _find_student(student_name: Optional[str] = None, student_id: Optional[int] = None):
    if student_id:
        record = _request("GET", f"/api/students/{student_id}")
        if "error" in record:
            return None, _dump(record)
        return record, None
    if not student_name:
        return None, _error("需要提供学员姓名 student_name 或 student_id。")
    keyword = student_name.strip()
    hits = [s for s in _students() if s.get("name") == keyword]
    if not hits:
        hits = [s for s in _students() if keyword in (s.get("name") or "")]
    if not hits:
        return None, _error(f"未找到学员「{student_name}」。")
    if len(hits) > 1:
        brief = [{"student_id": s["student_id"], "name": s.get("name"), "phone": s.get("phone")} for s in hits]
        return None, _dump({"error": f"「{student_name}」匹配到多名学员，请提供 student_id。", "candidates": brief})
    return hits[0], None


def _find_coach(coach_name: Optional[str] = None, coach_id: Optional[int] = None):
    if coach_id:
        record = _request("GET", f"/api/coaches/{coach_id}")
        if "error" in record:
            return None, _dump(record)
        return record, None
    if not coach_name:
        return None, _error("需要提供教练姓名 coach_name 或 coach_id。")
    keyword = coach_name.strip()
    hits = [c for c in _coaches() if c.get("name") == keyword]
    if not hits:
        hits = [c for c in _coaches() if keyword in (c.get("name") or "")]
    if not hits:
        return None, _error(f"未找到教练「{coach_name}」。")
    if len(hits) > 1:
        brief = [{"coach_id": c["coach_id"], "name": c.get("name"), "phone": c.get("phone")} for c in hits]
        return None, _dump({"error": f"「{coach_name}」匹配到多名教练，请提供 coach_id。", "candidates": brief})
    return hits[0], None


def _decorate_people(rows: list) -> list:
    names = _area_map()
    for row in rows:
        if isinstance(row, dict) and "area_id" in row:
            row["area_name"] = names.get(row.get("area_id"))
    return rows


# ---------------------------------------------------------------- 查询类


@tool
def list_areas() -> str:
    """查询全部区域（区域 ID 与名称）。新增学员/教练、按区域统计前先调用。"""
    return _dump(_areas())


@tool
def list_students(keyword: Optional[str] = None, area_name: Optional[str] = None) -> str:
    """查询学员列表。keyword 按姓名或手机号模糊匹配；area_name 按区域过滤。"""
    rows = _decorate_people(_students())
    if keyword:
        key = keyword.strip()
        rows = [r for r in rows if key in (r.get("name") or "") or key in (r.get("phone") or "")]
    if area_name:
        key = area_name.strip()
        rows = [r for r in rows if r.get("area_name") == key or (not r.get("area_name") and key == "未分配")]
    return _dump(rows)


@tool
def list_coaches(keyword: Optional[str] = None, area_name: Optional[str] = None) -> str:
    """查询教练列表（含负责车辆）。keyword 按姓名或手机号模糊匹配；area_name 按区域过滤。"""
    rows = _decorate_people(_coaches())
    if keyword:
        key = keyword.strip()
        rows = [r for r in rows if key in (r.get("name") or "") or key in (r.get("phone") or "")]
    if area_name:
        key = area_name.strip()
        rows = [r for r in rows if r.get("area_name") == key or (not r.get("area_name") and key == "未分配")]
    return _dump(rows)


@tool
def list_vehicles(vehicle_type: Optional[str] = None) -> str:
    """查询车辆列表。vehicle_type 只能为 SUV 或 轿车，不传表示全部。"""
    rows = _vehicles()
    if vehicle_type:
        rows = [r for r in rows if r.get("vehicle_type") == vehicle_type.strip()]
    return _dump(rows)


@tool
def list_coach_vehicles(coach_name: Optional[str] = None, coach_id: Optional[int] = None) -> str:
    """查询某位教练当前关联的车辆。"""
    coach, err = _find_coach(coach_name, coach_id)
    if err:
        return err
    data = _request("GET", f"/api/coaches/{coach['coach_id']}/vehicles")
    return _dump({"coach": coach.get("name"), "coach_id": coach["coach_id"], "vehicles": data})


@tool
def list_appointments(
    appointment_date: Optional[str] = None,
    status: Optional[str] = None,
    student_name: Optional[str] = None,
    coach_name: Optional[str] = None,
) -> str:
    """查询预约记录。appointment_date 格式 YYYY-MM-DD；status 为 待确认/已确认/已取消/已完成。"""
    if status and status not in APPOINTMENT_STATUS:
        return _error(f"status 只能是 {'/'.join(APPOINTMENT_STATUS)}")
    rows = _request("GET", "/api/appointments", {"page": 1, "page_size": 200})
    if not isinstance(rows, list):
        return _dump(rows)
    students = {s["student_id"]: s.get("name") for s in _students()}
    coaches = {c["coach_id"]: c.get("name") for c in _coaches()}
    for row in rows:
        row["student_name"] = students.get(row.get("student_id"))
        row["coach_name"] = coaches.get(row.get("coach_id"))
    if appointment_date:
        rows = [r for r in rows if r.get("appointment_date") == appointment_date.strip()]
    if status:
        rows = [r for r in rows if r.get("status") == status.strip()]
    if student_name:
        key = student_name.strip()
        rows = [r for r in rows if key in (r.get("student_name") or "")]
    if coach_name:
        key = coach_name.strip()
        rows = [r for r in rows if key in (r.get("coach_name") or "")]
    return _dump(rows)


@tool
def list_recharges(student_name: Optional[str] = None, student_id: Optional[int] = None) -> str:
    """查询充值记录（金额、课时、充值时间）。可按学员过滤。"""
    if student_name or student_id:
        student, err = _find_student(student_name, student_id)
        if err:
            return err
        data = _request("GET", f"/api/recharges/student/{student['student_id']}")
        return _dump({"student": student.get("name"), "recharges": data})
    data = _request("GET", "/api/recharges", {"page": 1, "page_size": 200})
    return _dump(data)


@tool
def get_balance(student_name: Optional[str] = None, student_id: Optional[int] = None) -> str:
    """查询学员剩余课时与余额明细（充值/课时消耗流水）。"""
    student, err = _find_student(student_name, student_id)
    if err:
        return err
    records = _request("GET", f"/api/balance-records/student/{student['student_id']}")
    if not isinstance(records, list):
        return _dump(records)
    latest = records[0] if records else {}
    return _dump(
        {
            "student": student.get("name"),
            "student_id": student["student_id"],
            "balance": latest.get("balance", 0),
            "hours": latest.get("hours", 0),
            "records": records,
        }
    )


@tool
def list_audit_logs(limit: int = 20, student_id: Optional[int] = None, coach_id: Optional[int] = None) -> str:
    """查询操作审计日志，默认最近 20 条，用于追溯谁在什么时间做了什么操作。"""
    if student_id:
        data = _request("GET", f"/api/audit-logs/student/{student_id}")
    elif coach_id:
        data = _request("GET", f"/api/audit-logs/coach/{coach_id}")
    else:
        data = _request("GET", "/api/audit-logs/", {"page": 1, "page_size": max(1, min(limit, 200))})
    if isinstance(data, list) and (student_id or coach_id):
        data = data[:limit]
    return _dump(data)


@tool
def area_statistics() -> str:
    """按区域汇总学员数、教练数、预约数、充值金额，用于区域经营分析。"""
    areas = _areas()
    students = _students()
    coaches = _coaches()
    appointments = _request("GET", "/api/appointments", {"page": 1, "page_size": 200})
    recharges = _request("GET", "/api/recharges", {"page": 1, "page_size": 200})
    if not isinstance(appointments, list):
        appointments = []
    if not isinstance(recharges, list):
        recharges = []
    student_area = {s["student_id"]: s.get("area_id") for s in students}
    result = []
    for area in areas:
        aid = area.get("area_id")
        area_students = [s for s in students if s.get("area_id") == aid]
        area_recharges = [r for r in recharges if student_area.get(r.get("student_id")) == aid]
        result.append(
            {
                "area_id": aid,
                "area_name": area.get("name"),
                "students": len(area_students),
                "coaches": len([c for c in coaches if c.get("area_id") == aid]),
                "appointments": len([a for a in appointments if student_area.get(a.get("student_id")) == aid]),
                "recharge_amount": round(sum(float(r.get("amount") or 0) for r in area_recharges), 2),
                "recharge_courses": sum(int(r.get("course_count") or 0) for r in area_recharges),
            }
        )
    return _dump(result)


# ---------------------------------------------------------------- 区域写操作


@tool
def create_area(name: str) -> str:
    """新增区域，name 为区域名称（不可重复）。"""
    return _dump(_request("POST", "/api/areas", body={"name": name.strip()}))


@tool
def update_area(area_id: int, name: str) -> str:
    """修改区域名称，area_id 可通过 list_areas 获取。"""
    return _dump(_request("PUT", f"/api/areas/{area_id}", body={"name": name.strip()}))


@tool
def delete_area(area_id: int) -> str:
    """删除区域。若区域下仍有学员或教练，业务后端会拒绝。"""
    return _dump(_request("DELETE", f"/api/areas/{area_id}"))


# ---------------------------------------------------------------- 学员写操作


@tool
def create_student(
    name: str, phone: str, area_name: Optional[str] = None, driving_years: int = 0, remark: Optional[str] = None
) -> str:
    """新增学员。phone 必须是 11 位手机号且唯一；area_name 必须已存在。"""
    area_id = None
    if area_name:
        area, err = _find_area(area_name)
        if err:
            return err
        area_id = area["area_id"]
    body = {"name": name.strip(), "phone": phone.strip(), "area_id": area_id, "driving_years": driving_years, "remark": remark}
    return _dump(_request("POST", "/api/students", body=body))


@tool
def update_student(
    student_id: int,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    area_name: Optional[str] = None,
    driving_years: Optional[int] = None,
    remark: Optional[str] = None,
) -> str:
    """修改学员资料，只需传入要变更的字段；area_name 会解析为区域 ID。"""
    current = _request("GET", f"/api/students/{student_id}")
    if "error" in current:
        return _dump(current)
    body = {}
    if name is not None:
        body["name"] = name.strip()
    if phone is not None:
        body["phone"] = phone.strip()
    if area_name is not None:
        area, err = _find_area(area_name)
        if err:
            return err
        body["area_id"] = area["area_id"]
    if driving_years is not None:
        body["driving_years"] = driving_years
    if remark is not None:
        body["remark"] = remark
    if not body:
        return _error("没有需要修改的字段。")
    return _dump(_request("PUT", f"/api/students/{student_id}", body=body))


@tool
def delete_student(student_id: int) -> str:
    """删除学员及其关联数据，操作不可恢复。"""
    return _dump(_request("DELETE", f"/api/students/{student_id}"))


# ---------------------------------------------------------------- 教练写操作


@tool
def create_coach(name: str, phone: str, area_name: Optional[str] = None) -> str:
    """新增教练。phone 必须是 11 位手机号且唯一；area_name 必须已存在。"""
    area_id = None
    if area_name:
        area, err = _find_area(area_name)
        if err:
            return err
        area_id = area["area_id"]
    body = {"name": name.strip(), "phone": phone.strip(), "area_id": area_id}
    return _dump(_request("POST", "/api/coaches", body=body))


@tool
def update_coach(
    coach_id: int,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    area_name: Optional[str] = None,
) -> str:
    """修改教练资料，只需传入要变更的字段。"""
    current = _request("GET", f"/api/coaches/{coach_id}")
    if "error" in current:
        return _dump(current)
    body = {}
    if name is not None:
        body["name"] = name.strip()
    if phone is not None:
        body["phone"] = phone.strip()
    if area_name is not None:
        area, err = _find_area(area_name)
        if err:
            return err
        body["area_id"] = area["area_id"]
    if not body:
        return _error("没有需要修改的字段。")
    return _dump(_request("PUT", f"/api/coaches/{coach_id}", body=body))


@tool
def delete_coach(coach_id: int) -> str:
    """删除教练及其车辆关联，操作不可恢复。"""
    return _dump(_request("DELETE", f"/api/coaches/{coach_id}"))


@tool
def assign_coach_vehicle(coach_id: int, vehicle_ids: list) -> str:
    """为教练设置可使用的车辆（覆盖式）。vehicle_ids 是车辆 ID 列表，可先通过 list_vehicles 查询。"""
    current = _request("GET", f"/api/coaches/{coach_id}")
    if "error" in current:
        return _dump(current)
    body = {
        "name": current.get("name"),
        "phone": current.get("phone"),
        "area_id": current.get("area_id"),
        "vehicle_ids": vehicle_ids,
    }
    return _dump(_request("PUT", f"/api/coaches/{coach_id}", body=body))


# ---------------------------------------------------------------- 车辆写操作


@tool
def create_vehicle(vehicle_type: str, brand: str, model: str) -> str:
    """新增车辆。vehicle_type 只能是 SUV 或 轿车。"""
    if vehicle_type.strip() not in VEHICLE_TYPES:
        return _error(f"vehicle_type 只能是 {'/'.join(VEHICLE_TYPES)}")
    body = {"vehicle_type": vehicle_type.strip(), "brand": brand.strip(), "model": model.strip()}
    return _dump(_request("POST", "/api/vehicles", body=body))


@tool
def update_vehicle(
    vehicle_id: int,
    vehicle_type: Optional[str] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """修改车辆信息，只需传入要变更的字段。"""
    if vehicle_type and vehicle_type.strip() not in VEHICLE_TYPES:
        return _error(f"vehicle_type 只能是 {'/'.join(VEHICLE_TYPES)}")
    body = {}
    if vehicle_type is not None:
        body["vehicle_type"] = vehicle_type.strip()
    if brand is not None:
        body["brand"] = brand.strip()
    if model is not None:
        body["model"] = model.strip()
    if not body:
        return _error("没有需要修改的字段。")
    return _dump(_request("PUT", f"/api/vehicles/{vehicle_id}", body=body))


@tool
def delete_vehicle(vehicle_id: int) -> str:
    """删除车辆及其教练关联，操作不可恢复。"""
    return _dump(_request("DELETE", f"/api/vehicles/{vehicle_id}"))


# ---------------------------------------------------------------- 预约写操作


@tool
def create_appointment(
    student_name: str,
    coach_name: str,
    appointment_date: str,
    start_time: int,
    end_time: int,
    status: str = "待确认",
) -> str:
    """创建预约。日期格式 YYYY-MM-DD；start_time/end_time 为 1-24 的小时且 end_time 必须大于 start_time。"""
    if status not in APPOINTMENT_STATUS:
        return _error(f"status 只能是 {'/'.join(APPOINTMENT_STATUS)}")
    if not (1 <= start_time <= 24 and 1 <= end_time <= 24 and end_time > start_time):
        return _error("start_time/end_time 必须在 1-24 之间，且 end_time 大于 start_time。")
    student, err = _find_student(student_name)
    if err:
        return err
    coach, err = _find_coach(coach_name)
    if err:
        return err
    body = {
        "student_id": student["student_id"],
        "coach_id": coach["coach_id"],
        "appointment_date": appointment_date.strip(),
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
    }
    return _dump(_request("POST", "/api/appointments", body=body))


@tool
def update_appointment(
    appointment_id: int,
    appointment_date: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    status: Optional[str] = None,
) -> str:
    """修改预约时间或状态。状态只能是 待确认/已确认/已取消/已完成。"""
    if status and status not in APPOINTMENT_STATUS:
        return _error(f"status 只能是 {'/'.join(APPOINTMENT_STATUS)}")
    body = {}
    if appointment_date is not None:
        body["appointment_date"] = appointment_date.strip()
    if start_time is not None:
        body["start_time"] = start_time
    if end_time is not None:
        body["end_time"] = end_time
    if status is not None:
        body["status"] = status
    if not body:
        return _error("没有需要修改的字段。")
    current = _request("GET", f"/api/appointments/{appointment_id}")
    if "error" in current:
        return _dump(current)
    merged_start = body.get("start_time", current.get("start_time"))
    merged_end = body.get("end_time", current.get("end_time"))
    if not (1 <= merged_start <= 24 and 1 <= merged_end <= 24 and merged_end > merged_start):
        return _error("预约时段必须在 1-24 之间，且结束时间大于开始时间。")
    return _dump(_request("PUT", f"/api/appointments/{appointment_id}", body=body))


@tool
def delete_appointment(appointment_id: int) -> str:
    """删除预约记录，操作不可恢复。"""
    return _dump(_request("DELETE", f"/api/appointments/{appointment_id}"))


# ---------------------------------------------------------------- 充值写操作


@tool
def create_recharge(
    student_name: str, amount: float, course_count: int, recharge_time: Optional[str] = None
) -> str:
    """为学员充值，amount 为金额（大于 0），course_count 为课时数（大于 0）。

    recharge_time 为充值时间，格式 YYYY-MM-DD HH:MM:SS；不传时自动取当前时间。
    """
    if amount <= 0 or course_count <= 0:
        return _error("充值金额与课时数都必须大于 0。")
    student, err = _find_student(student_name)
    if err:
        return err
    body = {
        "student_id": student["student_id"],
        "amount": amount,
        "course_count": course_count,
        "recharge_time": (recharge_time or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return _dump(_request("POST", "/api/recharges", body=body))


@tool
def update_recharge(
    recharge_id: int,
    amount: Optional[float] = None,
    course_count: Optional[int] = None,
    recharge_time: Optional[str] = None,
) -> str:
    """修改充值记录的金额、课时数或充值时间（recharge_time 格式 YYYY-MM-DD HH:MM:SS）。"""
    current = _request("GET", f"/api/recharges/{recharge_id}")
    if "error" in current:
        return _dump(current)
    body = {}
    if amount is not None:
        body["amount"] = amount
    if course_count is not None:
        body["course_count"] = course_count
    if recharge_time:
        body["recharge_time"] = recharge_time.strip()
    if not body:
        return _error("没有需要修改的字段。")
    if body.get("amount", current.get("amount")) <= 0 or body.get("course_count", current.get("course_count")) <= 0:
        return _error("充值金额与课时数都必须大于 0。")
    return _dump(_request("PUT", f"/api/recharges/{recharge_id}", body=body))


@tool
def delete_recharge(recharge_id: int) -> str:
    """删除充值记录（同时会回滚对应余额记录），操作不可恢复。"""
    return _dump(_request("DELETE", f"/api/recharges/{recharge_id}"))


QUERY_TOOLS = [
    list_areas,
    list_students,
    list_coaches,
    list_vehicles,
    list_coach_vehicles,
    list_appointments,
    list_recharges,
    get_balance,
    list_audit_logs,
    area_statistics,
]

WRITE_TOOLS = [
    create_area,
    update_area,
    delete_area,
    create_student,
    update_student,
    delete_student,
    create_coach,
    update_coach,
    delete_coach,
    assign_coach_vehicle,
    create_vehicle,
    update_vehicle,
    delete_vehicle,
    create_appointment,
    update_appointment,
    delete_appointment,
    create_recharge,
    update_recharge,
    delete_recharge,
]

ALL_TOOLS = QUERY_TOOLS + WRITE_TOOLS
