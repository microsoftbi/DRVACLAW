#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""驾驶智陪工作台 · 老赵技能 CLI

仅依赖 Python 标准库，供智能体通过命令行调用后端 REST API。
用法示例：
    python3 SKILLS/SKILL.py health
    python3 SKILLS/SKILL.py students
    python3 SKILLS/SKILL.py appointment-add --student-name 徐学员 --student-area 二七区 \
        --coach-name 赵教练 --coach-area 二七区 --date 2026-11-12 --start 9 --end 11

后端地址可用环境变量 DRVACLAW_API_BASE 覆盖，默认 http://127.0.0.1:8002
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

BASE_URL = os.environ.get("DRVACLAW_API_BASE", "http://127.0.0.1:8002").rstrip("/")
TIMEOUT = 15

STATUS_CHOICES = ["待确认", "已确认", "已取消", "已完成"]


def _dump(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


class ApiError(Exception):
    """接口或解析失败，携带供智能体判断的补充信息。"""

    def __init__(self, message, **extra):
        super().__init__(message)
        self.extra = extra


def _fail(message, **extra):
    raise ApiError(message, **extra)


def api(method, path, params=None, body=None):
    """发起一次 HTTP 请求并返回解析后的 JSON。"""
    url = BASE_URL + path
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        try:
            detail = json.loads(detail)
        except ValueError:
            pass
        _fail("接口调用失败（HTTP %s）" % exc.code, url=url, detail=detail)
    except urllib.error.URLError as exc:
        _fail("无法连接后端服务，请确认已执行 ./start.sh（端口 8002）",
              url=url, detail=str(exc.reason))


# ---------------------------------------------------------------- 解析辅助

def _areas():
    return api("GET", "/api/areas")


def _area_id(name):
    for area in _areas():
        if area["name"] == name:
            return area["area_id"]
    _fail("未找到区域：%s" % name, available=[a["name"] for a in _areas()])


def _students():
    return api("GET", "/api/students")


def _coaches():
    return api("GET", "/api/coaches")


def resolve_student(name=None, phone=None, area_name=None):
    """按手机号或姓名（可带区域）定位学员，重名时返回候选让用户选择。"""
    students = _students()
    if phone:
        hits = [s for s in students if s["phone"] == phone]
        if len(hits) == 1:
            return hits[0]
        if not hits:
            _fail("未找到手机号为 %s 的学员" % phone)
    area_id = _area_id(area_name) if area_name else None
    hits = [s for s in students if s["name"] == name]
    if area_id is not None:
        hits = [s for s in hits if s.get("area_id") == area_id]
    if not hits:
        _fail("未找到学员：%s%s" % (name, "（区域：%s）" % area_name if area_name else ""),
              available_names=sorted({s["name"] for s in students}))
    if len(hits) > 1:
        _fail("存在重名学员，请补充区域或手机号", candidates=hits)
    return hits[0]


def resolve_coach(name, area_name=None):
    coaches = _coaches()
    area_id = _area_id(area_name) if area_name else None
    hits = [c for c in coaches if c["name"] == name]
    if area_id is not None:
        hits = [c for c in hits if c.get("area_id") == area_id]
    if not hits:
        _fail("未找到教练：%s%s" % (name, "（区域：%s）" % area_name if area_name else ""),
              available_names=sorted({c["name"] for c in coaches}))
    if len(hits) > 1:
        _fail("存在重名教练，请补充区域", candidates=hits)
    return hits[0]


def _int_list(value):
    if not value:
        return []
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def _body(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}


# ---------------------------------------------------------------- 命令实现

def cmd_health(_):
    return api("GET", "/health")


def cmd_areas(_):
    return api("GET", "/api/areas")


def cmd_area_get(a):
    return api("GET", "/api/areas/%d" % a.id)


def cmd_area_create(a):
    return api("POST", "/api/areas", body={"name": a.name})


def cmd_area_update(a):
    return api("PUT", "/api/areas/%d" % a.id, body={"name": a.name})


def cmd_area_delete(a):
    return api("DELETE", "/api/areas/%d" % a.id)


def cmd_students(a):
    if a.student_id:
        return api("GET", "/api/students/%d" % a.student_id)
    return api("GET", "/api/students", {"page": a.page, "page_size": a.page_size})


def cmd_student_create(a):
    return api("POST", "/api/students", body=_body(
        name=a.name, phone=a.phone, area_id=a.area_id,
        driving_years=a.driving_years, remark=a.remark))


def cmd_student_update(a):
    return api("PUT", "/api/students/%d" % a.id, body=_body(
        name=a.name, phone=a.phone, area_id=a.area_id,
        driving_years=a.driving_years, remark=a.remark))


def cmd_student_delete(a):
    return api("DELETE", "/api/students/%d" % a.id)


def cmd_coaches(a):
    if a.coach_id:
        return api("GET", "/api/coaches/%d" % a.coach_id)
    return api("GET", "/api/coaches", {"page": a.page, "page_size": a.page_size})


def cmd_coach_vehicles(a):
    return api("GET", "/api/coaches/%d/vehicles" % a.id)


def cmd_coach_create(a):
    return api("POST", "/api/coaches", body=_body(
        name=a.name, phone=a.phone, area_id=a.area_id,
        vehicle_ids=_int_list(a.vehicle_ids)))


def cmd_coach_update(a):
    return api("PUT", "/api/coaches/%d" % a.id, body=_body(
        name=a.name, phone=a.phone, area_id=a.area_id,
        vehicle_ids=_int_list(a.vehicle_ids) if a.vehicle_ids else None))


def cmd_coach_delete(a):
    return api("DELETE", "/api/coaches/%d" % a.id)


def cmd_vehicles(a):
    if a.vehicle_id:
        return api("GET", "/api/vehicles/%d" % a.vehicle_id)
    return api("GET", "/api/vehicles", {"page": a.page, "page_size": a.page_size})


def cmd_vehicle_create(a):
    return api("POST", "/api/vehicles", body={
        "vehicle_type": a.vehicle_type, "brand": a.brand, "model": a.model})


def cmd_vehicle_update(a):
    return api("PUT", "/api/vehicles/%d" % a.id, body=_body(
        vehicle_type=a.vehicle_type, brand=a.brand, model=a.model))


def cmd_vehicle_delete(a):
    return api("DELETE", "/api/vehicles/%d" % a.id)


def cmd_appointments(a):
    if a.id:
        return api("GET", "/api/appointments/%d" % a.id)
    if a.date:
        return api("GET", "/api/appointments/date/%s" % a.date)
    if a.student_id:
        return api("GET", "/api/appointments/student/%d" % a.student_id)
    if a.coach_id:
        return api("GET", "/api/appointments/coach/%d" % a.coach_id)
    return api("GET", "/api/appointments", {"page": a.page, "page_size": a.page_size})


def cmd_appointment_create(a):
    _check_time_range(a.start, a.end)
    return api("POST", "/api/appointments", body={
        "student_id": a.student_id, "coach_id": a.coach_id,
        "appointment_date": a.date, "start_time": a.start, "end_time": a.end,
        "status": a.status})


def cmd_appointment_add(a):
    _check_time_range(a.start, a.end)
    student = resolve_student(name=a.student_name, phone=a.student_phone, area_name=a.student_area)
    coach = resolve_coach(a.coach_name, a.coach_area)
    return api("POST", "/api/appointments", body={
        "student_id": student["student_id"], "coach_id": coach["coach_id"],
        "appointment_date": a.date, "start_time": a.start, "end_time": a.end,
        "status": a.status})


def create_appointment(student_name, student_area, coach_name, coach_area,
                       date, start_time, end_time):
    """兼容旧版 appointment-creator 技能：按姓名+区域创建预约。

    返回 {"success": True, "appointment_id": n} 或 {"error": "..."}。
    """
    try:
        student = resolve_student(name=student_name, area_name=student_area)
        coach = resolve_coach(coach_name, coach_area)
        _check_time_range(start_time, end_time)
        created = api("POST", "/api/appointments", body={
            "student_id": student["student_id"], "coach_id": coach["coach_id"],
            "appointment_date": date, "start_time": start_time, "end_time": end_time,
            "status": "待确认"})
        return {"success": True, "appointment_id": created["appointment_id"]}
    except ApiError as exc:
        return {"error": str(exc)}


def cmd_appointment_update(a):
    if a.start is not None and a.end is not None:
        _check_time_range(a.start, a.end)
    return api("PUT", "/api/appointments/%d" % a.id, body=_body(
        student_id=a.student_id, coach_id=a.coach_id, appointment_date=a.date,
        start_time=a.start, end_time=a.end, status=a.status))


def cmd_appointment_confirm(a):
    return api("PUT", "/api/appointments/%d" % a.id, body={"status": "已确认"})


def cmd_appointment_delete(a):
    return api("DELETE", "/api/appointments/%d" % a.id)


def cmd_recharges(a):
    if a.id:
        return api("GET", "/api/recharges/%d" % a.id)
    if a.student_id:
        return api("GET", "/api/recharges/student/%d" % a.student_id)
    return api("GET", "/api/recharges", {"page": a.page, "page_size": a.page_size})


def cmd_recharge_create(a):
    return api("POST", "/api/recharges", body={
        "student_id": a.student_id, "amount": a.amount,
        "course_count": a.course_count,
        "recharge_time": a.recharge_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


def cmd_recharge_add(a):
    student = resolve_student(name=a.student_name, phone=a.phone, area_name=a.student_area)
    return api("POST", "/api/recharges", body={
        "student_id": student["student_id"], "amount": a.amount,
        "course_count": a.course_count,
        "recharge_time": a.recharge_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


def cmd_recharge_update(a):
    return api("PUT", "/api/recharges/%d" % a.id, body=_body(
        student_id=a.student_id, amount=a.amount,
        course_count=a.course_count, recharge_time=a.recharge_time))


def cmd_recharge_delete(a):
    return api("DELETE", "/api/recharges/%d" % a.id)


def cmd_balance(a):
    if a.id:
        return api("GET", "/api/balance-records/%d" % a.id)
    if a.student_id:
        return api("GET", "/api/balance-records/student/%d" % a.student_id)
    return api("GET", "/api/balance-records", {"page": a.page, "page_size": a.page_size})


def cmd_audit(a):
    if a.student_id:
        return api("GET", "/api/audit-logs/student/%d" % a.student_id)
    if a.coach_id:
        return api("GET", "/api/audit-logs/coach/%d" % a.coach_id)
    return api("GET", "/api/audit-logs/", {"page": a.page, "page_size": a.page_size})


def _check_time_range(start, end):
    if not (1 <= start <= 24 and 1 <= end <= 24):
        _fail("开始/结束时间必须为 1-24 的整数", start=start, end=end)
    if start >= end:
        _fail("结束时间必须晚于开始时间", start=start, end=end)


# ---------------------------------------------------------------- 参数定义

def build_parser():
    parser = argparse.ArgumentParser(description="驾驶智陪工作台 API 技能（老赵）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add(name, func, help_text):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=func)
        return p

    def paging(p):
        p.add_argument("--page", type=int)
        p.add_argument("--page-size", type=int, dest="page_size")

    def sid(p, dest="student_id"):
        p.add_argument("--student-id", type=int, dest=dest)

    add("health", cmd_health, "检查后端服务是否可用")
    add("areas", cmd_areas, "区域列表")

    p = add("area-get", cmd_area_get, "按 ID 查询区域")
    p.add_argument("--id", type=int, required=True)
    p = add("area-create", cmd_area_create, "新增区域")
    p.add_argument("--name", required=True)
    p = add("area-update", cmd_area_update, "修改区域名称")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--name", required=True)
    p = add("area-delete", cmd_area_delete, "删除区域（不可逆）")
    p.add_argument("--id", type=int, required=True)

    p = add("students", cmd_students, "学员列表，或按 --student-id 查询单个学员")
    paging(p)
    sid(p)
    p = add("student-create", cmd_student_create, "新增学员")
    p.add_argument("--name", required=True)
    p.add_argument("--phone", required=True)
    p.add_argument("--area-id", type=int, dest="area_id")
    p.add_argument("--driving-years", type=int, dest="driving_years", default=0)
    p.add_argument("--remark")
    p = add("student-update", cmd_student_update, "修改学员信息（仅传需要改的字段）")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--name")
    p.add_argument("--phone")
    p.add_argument("--area-id", type=int, dest="area_id")
    p.add_argument("--driving-years", type=int, dest="driving_years")
    p.add_argument("--remark")
    p = add("student-delete", cmd_student_delete, "删除学员（不可逆）")
    p.add_argument("--id", type=int, required=True)

    p = add("coaches", cmd_coaches, "教练列表，或按 --coach-id 查询单个教练")
    paging(p)
    p.add_argument("--coach-id", type=int, dest="coach_id")
    p = add("coach-vehicles", cmd_coach_vehicles, "查询教练名下车辆")
    p.add_argument("--id", type=int, required=True)
    p = add("coach-create", cmd_coach_create, "新增教练")
    p.add_argument("--name", required=True)
    p.add_argument("--phone", required=True)
    p.add_argument("--area-id", type=int, dest="area_id")
    p.add_argument("--vehicle-ids", dest="vehicle_ids", help="逗号分隔，如 1,2")
    p = add("coach-update", cmd_coach_update, "修改教练信息")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--name")
    p.add_argument("--phone")
    p.add_argument("--area-id", type=int, dest="area_id")
    p.add_argument("--vehicle-ids", dest="vehicle_ids")
    p = add("coach-delete", cmd_coach_delete, "删除教练（不可逆）")
    p.add_argument("--id", type=int, required=True)

    p = add("vehicles", cmd_vehicles, "车辆列表，或按 --vehicle-id 查询单辆车")
    paging(p)
    p.add_argument("--vehicle-id", type=int, dest="vehicle_id")
    p = add("vehicle-create", cmd_vehicle_create, "新增车辆")
    p.add_argument("--vehicle-type", dest="vehicle_type", choices=["SUV", "轿车"], required=True)
    p.add_argument("--brand", required=True)
    p.add_argument("--model", required=True)
    p = add("vehicle-update", cmd_vehicle_update, "修改车辆信息")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--vehicle-type", dest="vehicle_type", choices=["SUV", "轿车"])
    p.add_argument("--brand")
    p.add_argument("--model")
    p = add("vehicle-delete", cmd_vehicle_delete, "删除车辆（不可逆）")
    p.add_argument("--id", type=int, required=True)

    p = add("appointments", cmd_appointments, "预约查询：全部 / 按日期 / 按学员 / 按教练 / 按 ID")
    paging(p)
    p.add_argument("--id", type=int)
    p.add_argument("--date")
    p.add_argument("--student-id", type=int, dest="student_id")
    p.add_argument("--coach-id", type=int, dest="coach_id")
    p = add("appointment-create", cmd_appointment_create, "按 ID 创建预约")
    p.add_argument("--student-id", type=int, dest="student_id", required=True)
    p.add_argument("--coach-id", type=int, dest="coach_id", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--end", type=int, required=True)
    p.add_argument("--status", default="待确认", choices=STATUS_CHOICES)
    p = add("appointment-add", cmd_appointment_add, "按姓名/区域自动解析 ID 后创建预约")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--student-name", dest="student_name")
    g.add_argument("--student-phone", dest="student_phone")
    p.add_argument("--student-area", dest="student_area")
    p.add_argument("--coach-name", dest="coach_name", required=True)
    p.add_argument("--coach-area", dest="coach_area")
    p.add_argument("--date", required=True)
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--end", type=int, required=True)
    p.add_argument("--status", default="待确认", choices=STATUS_CHOICES)
    p = add("appointment-update", cmd_appointment_update, "修改预约（仅传需要改的字段）")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--student-id", type=int, dest="student_id")
    p.add_argument("--coach-id", type=int, dest="coach_id")
    p.add_argument("--date")
    p.add_argument("--start", type=int)
    p.add_argument("--end", type=int)
    p.add_argument("--status", choices=STATUS_CHOICES)
    p = add("appointment-confirm", cmd_appointment_confirm, "确认预约（状态改为已确认）")
    p.add_argument("--id", type=int, required=True)
    p = add("appointment-delete", cmd_appointment_delete, "删除预约（不可逆）")
    p.add_argument("--id", type=int, required=True)

    p = add("recharges", cmd_recharges, "充值记录查询：全部 / 按学员 / 按 ID")
    paging(p)
    p.add_argument("--id", type=int)
    sid(p)
    p = add("recharge-create", cmd_recharge_create, "按学员 ID 创建充值记录")
    p.add_argument("--student-id", type=int, dest="student_id", required=True)
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--course-count", type=int, dest="course_count", required=True)
    p.add_argument("--recharge-time", dest="recharge_time")
    p = add("recharge-add", cmd_recharge_add, "按手机号/姓名自动解析学员后创建充值")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--phone")
    g.add_argument("--student-name", dest="student_name")
    p.add_argument("--student-area", dest="student_area")
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--course-count", type=int, dest="course_count", required=True)
    p.add_argument("--recharge-time", dest="recharge_time")
    p = add("recharge-update", cmd_recharge_update, "修改充值记录")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--student-id", type=int, dest="student_id")
    p.add_argument("--amount", type=float)
    p.add_argument("--course-count", type=int, dest="course_count")
    p.add_argument("--recharge-time", dest="recharge_time")
    p = add("recharge-delete", cmd_recharge_delete, "删除充值记录（不可逆）")
    p.add_argument("--id", type=int, required=True)

    p = add("balance", cmd_balance, "余额记录查询：全部 / 按学员 / 按 ID")
    paging(p)
    p.add_argument("--id", type=int)
    sid(p)
    p = add("audit", cmd_audit, "操作审计：全部 / 按学员 / 按教练")
    paging(p)
    sid(p)
    p.add_argument("--coach-id", type=int, dest="coach_id")

    return parser


def main():
    args = build_parser().parse_args()
    try:
        result = args.func(args)
    except ApiError as exc:
        _dump({"error": str(exc), **exc.extra})
        sys.exit(1)
    if result is not None:
        _dump(result)


if __name__ == "__main__":
    main()
