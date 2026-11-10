#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驾驶智陪工作台 · UAT 验收测试脚本

覆盖：环境可达性、区域/车辆/学员/教练基础资料、预约全生命周期、
充值与余额记账、操作审计、端到端业务闭环。

运行方式（依赖仅标准库）：
    /Users/wadesong/Desktop/TEST/DRVACLAW/Backend/.venv/bin/python3 uat_test_suite.py

产物：
    report/UAT_TEST_REPORT.html   验收测试报告
    report/results.json           原始执行结果
    report/junit.xml              JUnit 标准结果
"""

import html
import json
import random
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

API = "http://127.0.0.1:8002"
WEB = "http://127.0.0.1:5174"
BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "report"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
SCREENSHOT_SCRIPT = BASE_DIR / "capture_screenshots.mjs"
RUN_ID = datetime.now().strftime("%Y%m%d%H%M%S")

CASES = []
CLEANUP = []          # (资源类型, 主键)
CTX = {}              # 用例间共享数据


# ---------------------------------------------------------------------------
# 基础能力：HTTP 客户端
# ---------------------------------------------------------------------------
def request(method, path, body=None, base=None, raw=False, headers=None, timeout=15):
    """发起 HTTP 请求，返回 (状态码, 响应体, 响应头, 耗时秒)。4xx/5xx 不抛异常。"""
    url = (base or API).rstrip("/") + path
    data = None
    hdrs = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", "replace")
            status, resp_headers = resp.status, resp.headers
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", "replace")
        status, resp_headers = exc.code, exc.headers
    elapsed = time.time() - started
    payload = text
    if not raw:
        try:
            payload = json.loads(text) if text else None
        except json.JSONDecodeError:
            payload = text
    return status, payload, resp_headers, elapsed


def call(method, path, body=None, expect=200, base=None):
    """带状态码断言的请求封装，返回 (响应体, 状态码)。"""
    status, payload, _headers, _elapsed = request(method, path, body=body, base=base)
    if status != expect:
        raise AssertionError("%s %s 期望 HTTP %s，实际 %s（%s）"
                             % (method, path, expect, status, _brief(payload)))
    return payload, status


def _brief(payload, limit=160):
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "..."


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def unique_phone(prefix="139"):
    return prefix + "".join(str(random.randint(0, 9)) for _ in range(8))


def remember(kind, resource_id):
    CLEANUP.append((kind, resource_id))


# ---------------------------------------------------------------------------
# 用例注册
# ---------------------------------------------------------------------------
class Case(object):
    def __init__(self, cid, module, title, priority, expected, fn):
        self.cid = cid
        self.module = module
        self.title = title
        self.priority = priority
        self.expected = expected
        self.fn = fn


def case(cid, module, title, priority, expected):
    def decorator(fn):
        CASES.append(Case(cid, module, title, priority, expected, fn))
        return fn
    return decorator


# ---------------------------------------------------------------------------
# 数据构造辅助
# ---------------------------------------------------------------------------
def first_area_id():
    areas, _ = call("GET", "/api/areas")
    check(isinstance(areas, list) and areas, "区域列表为空，无法构造测试数据")
    return areas[0]["area_id"]


def create_student(tag, driving_years=0, remark=None, area_id=None):
    body = {
        "name": "UAT学员-%s-%s" % (tag, RUN_ID[-6:]),
        "phone": unique_phone(),
        "area_id": area_id if area_id is not None else first_area_id(),
        "driving_years": driving_years,
        "remark": remark,
    }
    student, _ = call("POST", "/api/students", body)
    remember("student", student["student_id"])
    return student


def create_vehicle(tag, vehicle_type="SUV"):
    body = {"vehicle_type": vehicle_type, "brand": "UAT-品牌", "model": "UAT-型号-" + tag}
    vehicle, _ = call("POST", "/api/vehicles", body)
    remember("vehicle", vehicle["vehicle_id"])
    return vehicle


def create_appointment(student_id, coach_id, date, start, end, status="待确认"):
    body = {
        "student_id": student_id,
        "coach_id": coach_id,
        "appointment_date": date,
        "start_time": start,
        "end_time": end,
        "status": status,
    }
    appointment, _ = call("POST", "/api/appointments", body)
    remember("appointment", appointment["appointment_id"])
    return appointment


def create_recharge(student_id, amount=1000, course_count=10, recharge_time=None):
    body = {
        "student_id": student_id,
        "amount": amount,
        "course_count": course_count,
        "recharge_time": recharge_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    recharge, _ = call("POST", "/api/recharges", body)
    remember("recharge", recharge["recharge_id"])
    return recharge


def balance_records_of(student_id):
    records, _ = call("GET", "/api/balance-records/student/%s" % student_id)
    check(isinstance(records, list), "余额记录返回格式异常：%s" % _brief(records))
    return records


def audit_logs_of_student(student_id):
    logs, _ = call("GET", "/api/audit-logs/student/%s" % student_id)
    check(isinstance(logs, list), "审计日志返回格式异常：%s" % _brief(logs))
    return logs


# ---------------------------------------------------------------------------
# 清理
# ---------------------------------------------------------------------------
CLEANUP_PATHS = {
    "appointment": "/api/appointments/%s",
    "recharge": "/api/recharges/%s",
    "coach": "/api/coaches/%s",
    "vehicle": "/api/vehicles/%s",
    "student": "/api/students/%s",
    "area": "/api/areas/%s",
}
CLEANUP_ORDER = ["appointment", "recharge", "coach", "vehicle", "student", "area"]


def cleanup_all():
    """按依赖顺序删除本次创建的数据，忽略删除失败。"""
    removed = 0
    for kind in CLEANUP_ORDER:
        for item_kind, resource_id in list(CLEANUP):
            if item_kind != kind:
                continue
            try:
                status, _payload, _h, _e = request("DELETE", CLEANUP_PATHS[kind] % resource_id)
                if status in (200, 404):
                    removed += 1
            except Exception:
                pass
            CLEANUP.remove((item_kind, resource_id))
    return removed


# ---------------------------------------------------------------------------
# 关键步骤截图：每条用例执行后立即截取对应业务页面
# ---------------------------------------------------------------------------
class ScreenshotSession(object):
    """常驻 Node 截图服务，复用同一个无头 Chrome，避免每条用例重启浏览器。"""

    def __init__(self):
        self.proc = None
        self.error = None

    def start(self):
        if not SCREENSHOT_SCRIPT.exists():
            self.error = "缺少截图脚本 %s" % SCREENSHOT_SCRIPT
            return False
        try:
            self.proc = subprocess.Popen(
                ["node", str(SCREENSHOT_SCRIPT), str(SCREENSHOT_DIR)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, bufsize=1, encoding="utf-8")
            line = self.proc.stdout.readline()
            ready = json.loads(line.strip() or "{}")
            if not ready.get("ready"):
                raise RuntimeError(ready.get("error") or "截图服务未就绪")
            return True
        except Exception as exc:
            self.error = str(exc)
            self.proc = None
            return False

    def capture(self, case_id, url, focus, title, caption, status):
        if not self.proc:
            return None
        payload = {
            "case_id": case_id, "url": url, "focus": focus or "",
            "title": title, "caption": caption, "status": status,
            "out": str(SCREENSHOT_DIR / (case_id + ".jpg")),
        }
        try:
            self.proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self.proc.stdin.flush()
            line = self.proc.stdout.readline()
            result = json.loads(line.strip() or "{}")
        except Exception as exc:
            self.error = str(exc)
            return None
        return result.get("path") if result.get("ok") else None

    def stop(self):
        if not self.proc:
            return
        try:
            self.proc.stdin.write('{"exit": true}\n')
            self.proc.stdin.flush()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()
        finally:
            self.proc = None


SHOT_ROUTES = {
    "区域管理": "/areas",
    "车辆管理": "/vehicles",
    "学员管理": "/students",
    "教练管理": "/coaches",
    "预约管理": "/appointments",
    "充值管理": "/recharges",
    "余额记录": "/balance-query",
    "操作审计": "/audit-logs",
    "端到端": "/balance-query",
}

# 直接展示后端原始响应，作为错误语义（404）的现场证据
SHOT_RAW = {
    "AREA-06": "/api/areas/999999",
    "VEH-06": "/api/vehicles/999999",
    "STU-06": "/api/students/999999",
    "COA-07": "/api/coaches/999999",
    "APT-10": "/api/appointments/999999",
    "APT-11": "/api/appointments/999999",
    "REC-06": "/api/recharges/999999",
    "BAL-03": "/api/balance-records/999999",
    "AUD-04": "/api/audit-logs/student/999999999",
}

SHOT_ENV = {
    "ENV-01": (API + "/", ""),
    "ENV-02": (API + "/health", ""),
    "ENV-03": (WEB + "/", ""),
    "ENV-04": (API + "/docs", ""),
    "ENV-05": (WEB + "/appointments", ""),
}

SHOT_CAPTIONS = {
    "AREA-05": "重复区域名称被拒绝（HTTP 400），列表未新增记录",
    "AREA-07": "区域已删除，列表中不再出现该区域",
    "VEH-04": "非法车型被拒绝（HTTP 400/422），未落库",
    "VEH-07": "车辆已删除，列表中不再出现该车辆",
    "STU-05": "重复手机号被拒绝（HTTP 400），未新增学员",
    "STU-07": "学员已删除，列表中不再出现该学员",
    "COA-06": "重复手机号被拒绝（HTTP 400），未新增教练",
    "COA-08": "教练已删除，列表中不再出现该教练",
    "APT-08": "非法状态被拒绝（HTTP 400），未生成预约",
    "APT-09": "非法时段被拒绝（HTTP 400），未生成预约",
    "APT-12": "预约已删除，列表中不再出现该预约",
    "APT-14": "引用不存在学员被拒绝（HTTP 400），未产生脏数据",
    "REC-05": "充值已删除，关联余额记录同步清理",
    "E2E-01": "端到端闭环：充值 10 课时 → 完成预约扣减 2 → 结余 8",
}

DELETED_CASES = ("AREA-07", "VEH-07", "STU-07", "COA-08", "APT-12", "REC-05")


def _ctx_name(key):
    record = CTX.get(key) or {}
    return record.get("name", "")


def shot_focus(case_id):
    if case_id in ("AREA-02", "AREA-03", "AREA-04"):
        return CTX.get("area_name", "")
    if case_id == "VEH-02":
        return "UAT-型号-A"
    if case_id == "VEH-03":
        return "UAT-型号-B"
    if case_id == "VEH-05":
        return "UAT-型号A-改"
    if case_id in ("STU-02", "STU-03", "STU-04"):
        return _ctx_name("student_a")
    if case_id in ("COA-02", "COA-03", "COA-04", "COA-05", "COA-06"):
        return _ctx_name("coach")
    if case_id in ("APT-02", "APT-03", "APT-04", "APT-05", "APT-06", "APT-07"):
        return APT_DATE
    if case_id == "APT-13":
        return _ctx_name("student_apt13")
    if case_id in ("REC-01", "REC-02", "REC-03", "REC-04"):
        return _ctx_name("student_rec")
    if case_id == "BAL-02":
        return _ctx_name("student_apt13")
    if case_id == "AUD-02":
        return _ctx_name("student_a")
    if case_id == "AUD-03":
        return "确认预约课程"
    if case_id == "E2E-01":
        return "UAT学员-闭环"
    return ""


def shot_spec(item):
    """返回 (.url, 关键数据定位文本, 截图说明)。"""
    if item.cid in SHOT_ENV:
        url, focus = SHOT_ENV[item.cid]
        return url, focus, SHOT_CAPTIONS.get(item.cid, item.expected)
    if item.cid in SHOT_RAW:
        return API + SHOT_RAW[item.cid], "", SHOT_CAPTIONS.get(item.cid, item.expected)
    route = SHOT_ROUTES.get(item.module)
    url = WEB + route if route else WEB + "/"
    focus = shot_focus(item.cid)
    if item.cid in DELETED_CASES:
        focus = ""
    caption = SHOT_CAPTIONS.get(item.cid, item.expected)
    return url, focus, caption


# ===========================================================================
# 5.1 环境可达性 ENV
# ===========================================================================
@case("ENV-01", "环境", "后端欢迎接口", "P0", "HTTP 200 且 message=欢迎使用驾驶智陪工作台 API")
def env_01():
    payload, _ = call("GET", "/")
    check(isinstance(payload, dict) and "驾驶智陪工作台" in payload.get("message", ""),
          "message 不符：%s" % _brief(payload))
    return "HTTP 200，message=%s" % payload["message"]


@case("ENV-02", "环境", "健康检查", "P0", "HTTP 200 且 status=ok")
def env_02():
    payload, _ = call("GET", "/health")
    check(payload.get("status") == "ok", "status=%s" % payload.get("status"))
    return "HTTP 200，status=ok"


@case("ENV-03", "环境", "前端页面可访问", "P0", "HTTP 200 且 title=驾驶智陪工作台")
def env_03():
    status, body, _h, _e = request("GET", "/", base=WEB, raw=True,
                                   headers={"Accept": "text/html"})
    check(status == 200, "前端页面期望 HTTP 200，实际 %s" % status)
    check("<title>驾驶智陪工作台</title>" in body, "页面标题未匹配，页面长度 %s" % len(body))
    return "HTTP 200，<title>驾驶智陪工作台</title>"


@case("ENV-04", "环境", "API 文档可访问", "P1", "HTTP 200 且包含 Swagger UI")
def env_04():
    status, body, _h, _e = request("GET", "/docs", raw=True)
    check(status == 200, "文档期望 HTTP 200，实际 %s" % status)
    check("swagger-ui" in body, "文档页面未包含 swagger-ui 标识")
    return "HTTP 200，包含 Swagger UI"


@case("ENV-05", "环境", "跨域预检", "P1", "HTTP 200 且返回 Access-Control-Allow-Origin")
def env_05():
    headers = {
        "Origin": WEB,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }
    status, _p, resp_headers, _e = request("OPTIONS", "/api/students", headers=headers)
    allow = resp_headers.get("Access-Control-Allow-Origin")
    check(status == 200, "预检期望 HTTP 200，实际 %s" % status)
    check(bool(allow), "响应缺少 Access-Control-Allow-Origin 头")
    return "HTTP 200，Access-Control-Allow-Origin=%s" % allow


# ===========================================================================
# 5.2 区域管理 AREA
# ===========================================================================
@case("AREA-01", "区域管理", "区域列表查询", "P0", "HTTP 200，数量≥10，字段完整")
def area_01():
    areas, _ = call("GET", "/api/areas")
    check(isinstance(areas, list), "返回不是数组")
    check(len(areas) >= 10, "区域数量不足 10，实际 %s" % len(areas))
    for item in areas[:3]:
        check("area_id" in item and "name" in item, "字段缺失：%s" % _brief(item))
    return "HTTP 200，共 %s 条区域" % len(areas)


@case("AREA-02", "区域管理", "新增区域", "P0", "HTTP 200，返回新 ID 且名称一致")
def area_02():
    name = "UAT区域-%s" % RUN_ID[-6:]
    area, _ = call("POST", "/api/areas", {"name": name})
    remember("area", area["area_id"])
    CTX["area_id"] = area["area_id"]
    CTX["area_name"] = name
    check(area.get("name") == name, "name 回显不符：%s" % area.get("name"))
    return "HTTP 200，area_id=%s，name=%s" % (area["area_id"], area["name"])


@case("AREA-03", "区域管理", "区域详情查询", "P0", "HTTP 200，字段与新建一致")
def area_03():
    area, _ = call("GET", "/api/areas/%s" % CTX["area_id"])
    check(area.get("name") == CTX["area_name"], "名称不符：%s" % area.get("name"))
    return "HTTP 200，area_id=%s，name=%s" % (area["area_id"], area["name"])


@case("AREA-04", "区域管理", "区域重命名", "P1", "HTTP 200，名称更新")
def area_04():
    new_name = "UAT区域-已更新-%s" % RUN_ID[-4:]
    area, _ = call("PUT", "/api/areas/%s" % CTX["area_id"], {"name": new_name})
    CTX["area_name"] = new_name
    check(area.get("name") == new_name, "名称未更新：%s" % area.get("name"))
    return "HTTP 200，name=%s" % area["name"]


@case("AREA-05", "区域管理", "区域名称唯一性", "P1", "重复名称被拒绝，HTTP 400")
def area_05():
    status, payload, _h, _e = request("POST", "/api/areas", {"name": CTX["area_name"]})
    check(status == 400, "重复名称期望 HTTP 400，实际 %s（%s）" % (status, _brief(payload)))
    return "HTTP 400，detail=%s" % payload.get("detail", "") if isinstance(payload, dict) else "HTTP 400"


@case("AREA-06", "区域管理", "查询不存在区域", "P1", "HTTP 404 且 detail=区域不存在")
def area_06():
    status, payload, _h, _e = request("GET", "/api/areas/999999")
    check(status == 404, "期望 HTTP 404，实际 %s" % status)
    check(isinstance(payload, dict) and payload.get("detail") == "区域不存在",
          "detail 不符：%s" % _brief(payload))
    return "HTTP 404，detail=区域不存在"


@case("AREA-07", "区域管理", "删除区域", "P1", "删除成功，再次查询返回 404")
def area_07():
    area_id = CTX["area_id"]
    payload, _ = call("DELETE", "/api/areas/%s" % area_id)
    check(payload.get("message") == "删除成功", "message 不符：%s" % _brief(payload))
    status, _p, _h, _e = request("GET", "/api/areas/%s" % area_id)
    check(status == 404, "删除后期望 HTTP 404，实际 %s" % status)
    CLEANUP[:] = [item for item in CLEANUP if item != ("area", area_id)]
    return "HTTP 200 删除成功，复查 HTTP 404"


# ===========================================================================
# 5.3 车辆管理 VEH
# ===========================================================================
@case("VEH-01", "车辆管理", "车辆列表与车型合法性", "P0", "HTTP 200，数量≥10，车型∈{SUV,轿车}")
def veh_01():
    vehicles, _ = call("GET", "/api/vehicles")
    check(isinstance(vehicles, list) and len(vehicles) >= 10,
          "车辆数量不足 10，实际 %s" % (len(vehicles) if isinstance(vehicles, list) else vehicles))
    bad = [v for v in vehicles if v.get("vehicle_type") not in ("SUV", "轿车")]
    check(not bad, "存在非法车型：%s" % _brief(bad[:3]))
    return "HTTP 200，共 %s 辆车，车型合法" % len(vehicles)


@case("VEH-02", "车辆管理", "新增 SUV 车辆", "P0", "HTTP 200，字段回显一致")
def veh_02():
    vehicle = create_vehicle("A", "SUV")
    CTX["vehicle_suv"] = vehicle["vehicle_id"]
    check(vehicle.get("vehicle_type") == "SUV", "车型不符：%s" % vehicle.get("vehicle_type"))
    return "HTTP 200，vehicle_id=%s，SUV %s %s" % (
        vehicle["vehicle_id"], vehicle["brand"], vehicle["model"])


@case("VEH-03", "车辆管理", "新增轿车", "P0", "HTTP 200，vehicle_type=轿车")
def veh_03():
    vehicle = create_vehicle("B", "轿车")
    CTX["vehicle_sedan"] = vehicle["vehicle_id"]
    check(vehicle.get("vehicle_type") == "轿车", "车型不符：%s" % vehicle.get("vehicle_type"))
    return "HTTP 200，vehicle_id=%s，轿车 %s %s" % (
        vehicle["vehicle_id"], vehicle["brand"], vehicle["model"])


@case("VEH-04", "车辆管理", "非法车型校验", "P1", "请求被拒绝（400/422），不落库")
def veh_04():
    body = {"vehicle_type": "跑车", "brand": "UAT-品牌", "model": "UAT-非法车型"}
    status, payload, _h, _e = request("POST", "/api/vehicles", body)
    check(status in (400, 422), "非法车型期望 400/422，实际 %s（%s）" % (status, _brief(payload)))
    return "HTTP %s，非法车型被拒绝" % status


@case("VEH-05", "车辆管理", "修改车辆型号", "P1", "HTTP 200，model 已更新")
def veh_05():
    new_model = "UAT-型号A-改"
    vehicle, _ = call("PUT", "/api/vehicles/%s" % CTX["vehicle_suv"], {"model": new_model})
    check(vehicle.get("model") == new_model, "model 未更新：%s" % vehicle.get("model"))
    return "HTTP 200，model=%s" % vehicle["model"]


@case("VEH-06", "车辆管理", "查询不存在车辆", "P1", "HTTP 404 且 detail=车辆不存在")
def veh_06():
    status, payload, _h, _e = request("GET", "/api/vehicles/999999")
    check(status == 404, "期望 HTTP 404，实际 %s" % status)
    check(isinstance(payload, dict) and payload.get("detail") == "车辆不存在",
          "detail 不符：%s" % _brief(payload))
    return "HTTP 404，detail=车辆不存在"


@case("VEH-07", "车辆管理", "删除车辆", "P1", "删除成功，再次查询 404")
def veh_07():
    vehicle = create_vehicle("TEMP", "SUV")
    payload, _ = call("DELETE", "/api/vehicles/%s" % vehicle["vehicle_id"])
    check(payload.get("message") == "删除成功", "message 不符：%s" % _brief(payload))
    status, _p, _h, _e = request("GET", "/api/vehicles/%s" % vehicle["vehicle_id"])
    check(status == 404, "删除后期望 HTTP 404，实际 %s" % status)
    CLEANUP[:] = [item for item in CLEANUP if item != ("vehicle", vehicle["vehicle_id"])]
    return "HTTP 200 删除成功，复查 HTTP 404"


# ===========================================================================
# 5.4 学员管理 STU
# ===========================================================================
@case("STU-01", "学员管理", "学员列表", "P0", "HTTP 200，数量≥10，字段完整")
def stu_01():
    students, _ = call("GET", "/api/students")
    check(isinstance(students, list) and len(students) >= 10,
          "学员数量不足 10，实际 %s" % (len(students) if isinstance(students, list) else students))
    for key in ("student_id", "name", "phone", "driving_years", "register_time"):
        check(key in students[0], "字段缺失：%s" % key)
    return "HTTP 200，共 %s 名学员" % len(students)


@case("STU-02", "学员管理", "新增学员（驾龄/备注）", "P0", "HTTP 200，驾龄=3、备注回显、注册时间生成")
def stu_02():
    student = create_student("A", driving_years=3, remark="UAT自动化测试学员")
    CTX["student_a"] = student
    check(student.get("driving_years") == 3, "驾龄不符：%s" % student.get("driving_years"))
    check(student.get("remark") == "UAT自动化测试学员", "备注不符：%s" % student.get("remark"))
    check(bool(student.get("register_time")), "注册时间为空")
    return "HTTP 200，student_id=%s，驾龄=%s，注册时间=%s" % (
        student["student_id"], student["driving_years"], student["register_time"])


@case("STU-03", "学员管理", "学员详情", "P0", "HTTP 200，字段与新建一致")
def stu_03():
    student_id = CTX["student_a"]["student_id"]
    student, _ = call("GET", "/api/students/%s" % student_id)
    for key in ("name", "phone", "area_id", "driving_years", "remark"):
        check(student.get(key) == CTX["student_a"].get(key), "字段 %s 不一致" % key)
    return "HTTP 200，%s / %s / 驾龄 %s" % (student["name"], student["phone"], student["driving_years"])


@case("STU-04", "学员管理", "修改驾龄与备注", "P1", "HTTP 200，驾龄=5、备注更新")
def stu_04():
    base = CTX["student_a"]
    body = {
        "name": base["name"],
        "phone": base["phone"],
        "area_id": base["area_id"],
        "driving_years": 5,
        "remark": "UAT备注更新",
    }
    student, _ = call("PUT", "/api/students/%s" % base["student_id"], body)
    check(student.get("driving_years") == 5, "驾龄未更新：%s" % student.get("driving_years"))
    check(student.get("remark") == "UAT备注更新", "备注未更新：%s" % student.get("remark"))
    CTX["student_a"].update(student)
    return "HTTP 200，驾龄=5，备注=UAT备注更新"


@case("STU-05", "学员管理", "手机号唯一性", "P1", "重复手机号被拒绝，HTTP 400")
def stu_05():
    body = {
        "name": "UAT学员-重复手机号",
        "phone": CTX["student_a"]["phone"],
        "area_id": CTX["student_a"]["area_id"],
        "driving_years": 1,
        "remark": None,
    }
    status, payload, _h, _e = request("POST", "/api/students", body)
    check(status == 400, "重复手机号期望 HTTP 400，实际 %s（%s）" % (status, _brief(payload)))
    return "HTTP 400，手机号唯一约束生效"


@case("STU-06", "学员管理", "查询不存在学员", "P1", "HTTP 404 且 detail=学员不存在")
def stu_06():
    status, payload, _h, _e = request("GET", "/api/students/999999")
    check(status == 404, "期望 HTTP 404，实际 %s" % status)
    check(isinstance(payload, dict) and payload.get("detail") == "学员不存在",
          "detail 不符：%s" % _brief(payload))
    return "HTTP 404，detail=学员不存在"


@case("STU-07", "学员管理", "删除学员", "P1", "删除成功，再次查询 404")
def stu_07():
    student = create_student("TEMP")
    payload, _ = call("DELETE", "/api/students/%s" % student["student_id"])
    check(payload.get("message") == "删除成功", "message 不符：%s" % _brief(payload))
    status, _p, _h, _e = request("GET", "/api/students/%s" % student["student_id"])
    check(status == 404, "删除后期望 HTTP 404，实际 %s" % status)
    CLEANUP[:] = [item for item in CLEANUP if item != ("student", student["student_id"])]
    return "HTTP 200 删除成功，复查 HTTP 404"


# ===========================================================================
# 5.5 教练管理 COA
# ===========================================================================
@case("COA-01", "教练管理", "教练列表含车辆关联", "P0", "HTTP 200，数量≥5，含 vehicle_ids 数组")
def coa_01():
    coaches, _ = call("GET", "/api/coaches")
    check(isinstance(coaches, list) and len(coaches) >= 5,
          "教练数量不足 5，实际 %s" % (len(coaches) if isinstance(coaches, list) else coaches))
    for item in coaches:
        check(isinstance(item.get("vehicle_ids"), list), "vehicle_ids 不是数组：%s" % _brief(item))
    return "HTTP 200，共 %s 名教练，均含 vehicle_ids" % len(coaches)


@case("COA-02", "教练管理", "新增教练并关联两辆车", "P0", "HTTP 200，vehicle_ids 含两辆车")
def coa_02():
    body = {
        "name": "UAT教练A-%s" % RUN_ID[-6:],
        "phone": unique_phone("138"),
        "area_id": first_area_id(),
        "vehicle_ids": [CTX["vehicle_suv"], CTX["vehicle_sedan"]],
    }
    coach, _ = call("POST", "/api/coaches", body)
    remember("coach", coach["coach_id"])
    CTX["coach"] = coach
    ids = coach.get("vehicle_ids") or []
    check(set(ids) == set(body["vehicle_ids"]), "关联车辆不符：%s" % ids)
    return "HTTP 200，coach_id=%s，关联车辆=%s" % (coach["coach_id"], ids)


@case("COA-03", "教练管理", "教练详情含车辆", "P0", "HTTP 200，vehicle_ids 与创建一致")
def coa_03():
    coach, _ = call("GET", "/api/coaches/%s" % CTX["coach"]["coach_id"])
    check(set(coach.get("vehicle_ids") or []) == set(CTX["coach"]["vehicle_ids"]),
          "vehicle_ids 不一致：%s" % coach.get("vehicle_ids"))
    return "HTTP 200，coach_id=%s，vehicle_ids=%s" % (coach["coach_id"], coach["vehicle_ids"])


@case("COA-04", "教练管理", "教练车辆明细", "P0", "HTTP 200，返回 2 辆车且字段完整")
def coa_04():
    vehicles, _ = call("GET", "/api/coaches/%s/vehicles" % CTX["coach"]["coach_id"])
    check(isinstance(vehicles, list) and len(vehicles) == 2, "车辆明细数量不符：%s" % _brief(vehicles))
    returned = set(v["vehicle_id"] for v in vehicles)
    check(returned == set(CTX["coach"]["vehicle_ids"]), "车辆 ID 不一致：%s" % returned)
    for v in vehicles:
        for key in ("vehicle_type", "brand", "model"):
            check(key in v, "车辆字段缺失：%s" % key)
    return "HTTP 200，共 2 辆车：%s" % sorted(returned)


@case("COA-05", "教练管理", "调整车辆关联", "P1", "HTTP 200，vehicle_ids 仅保留第二辆车")
def coa_05():
    target = [CTX["vehicle_sedan"]]
    coach, _ = call("PUT", "/api/coaches/%s" % CTX["coach"]["coach_id"], {"vehicle_ids": target})
    check(coach.get("vehicle_ids") == target, "关联未被替换：%s" % coach.get("vehicle_ids"))
    CTX["coach"]["vehicle_ids"] = target
    return "HTTP 200，vehicle_ids=%s" % coach["vehicle_ids"]


@case("COA-06", "教练管理", "教练手机号唯一性", "P1", "重复手机号被拒绝，HTTP 400")
def coa_06():
    base = CTX["coach"]
    body = {"name": "UAT教练-重复手机号", "phone": base["phone"], "area_id": base["area_id"]}
    status, payload, _h, _e = request("POST", "/api/coaches", body)
    check(status == 400, "重复手机号期望 HTTP 400，实际 %s（%s）" % (status, _brief(payload)))
    return "HTTP 400，手机号唯一约束生效"


@case("COA-07", "教练管理", "查询不存在教练", "P1", "HTTP 404 且 detail=教练不存在")
def coa_07():
    status, payload, _h, _e = request("GET", "/api/coaches/999999")
    check(status == 404, "期望 HTTP 404，实际 %s" % status)
    check(isinstance(payload, dict) and payload.get("detail") == "教练不存在",
          "detail 不符：%s" % _brief(payload))
    return "HTTP 404，detail=教练不存在"


@case("COA-08", "教练管理", "删除教练", "P1", "删除成功，再次查询 404")
def coa_08():
    body = {"name": "UAT教练-临时", "phone": unique_phone("138"), "area_id": first_area_id()}
    coach, _ = call("POST", "/api/coaches", body)
    payload, _ = call("DELETE", "/api/coaches/%s" % coach["coach_id"])
    check(payload.get("message") == "删除成功", "message 不符：%s" % _brief(payload))
    status, _p, _h, _e = request("GET", "/api/coaches/%s" % coach["coach_id"])
    check(status == 404, "删除后期望 HTTP 404，实际 %s" % status)
    CLEANUP[:] = [item for item in CLEANUP if item != ("coach", coach["coach_id"])]
    return "HTTP 200 删除成功，复查 HTTP 404"


# ===========================================================================
# 5.6 预约管理 APT
# ===========================================================================
APT_DATE = "2027-01-05"


@case("APT-01", "预约管理", "预约列表", "P0", "HTTP 200，数量≥30，字段完整")
def apt_01():
    appointments, _ = call("GET", "/api/appointments")
    check(isinstance(appointments, list) and len(appointments) >= 30,
          "预约数量不足 30，实际 %s" % (len(appointments) if isinstance(appointments, list) else appointments))
    for key in ("appointment_id", "student_id", "coach_id", "appointment_date",
                "start_time", "end_time", "status", "create_time"):
        check(key in appointments[0], "字段缺失：%s" % key)
    return "HTTP 200，共 %s 条预约" % len(appointments)


@case("APT-02", "预约管理", "创建待确认预约", "P0", "HTTP 200，字段回显且 create_time 生成")
def apt_02():
    appointment = create_appointment(CTX["student_a"]["student_id"],
                                     CTX["coach"]["coach_id"], APT_DATE, 10, 12)
    CTX["appointment"] = appointment
    check(appointment.get("status") == "待确认", "状态不符：%s" % appointment.get("status"))
    check(str(appointment.get("appointment_date")) == APT_DATE, "日期不符")
    check(bool(appointment.get("create_time")), "create_time 为空")
    return "HTTP 200，appointment_id=%s，%s 10:00-12:00，状态=待确认" % (
        appointment["appointment_id"], appointment["appointment_date"])


@case("APT-03", "预约管理", "预约详情", "P0", "HTTP 200，与创建数据一致")
def apt_03():
    appointment, _ = call("GET", "/api/appointments/%s" % CTX["appointment"]["appointment_id"])
    for key in ("student_id", "coach_id", "appointment_date", "start_time", "end_time", "status"):
        check(str(appointment.get(key)) == str(CTX["appointment"].get(key)), "字段 %s 不一致" % key)
    return "HTTP 200，appointment_id=%s，状态=%s" % (appointment["appointment_id"], appointment["status"])


@case("APT-04", "预约管理", "按学员查询预约", "P0", "HTTP 200，结果含本预约")
def apt_04():
    appointments, _ = call("GET", "/api/appointments/student/%s" % CTX["student_a"]["student_id"])
    ids = [a["appointment_id"] for a in appointments]
    check(CTX["appointment"]["appointment_id"] in ids, "结果未包含本预约，共 %s 条" % len(ids))
    return "HTTP 200，该学员共 %s 条预约，包含 #%s" % (len(ids), CTX["appointment"]["appointment_id"])


@case("APT-05", "预约管理", "按教练查询预约", "P0", "HTTP 200，结果含本预约")
def apt_05():
    appointments, _ = call("GET", "/api/appointments/coach/%s" % CTX["coach"]["coach_id"])
    ids = [a["appointment_id"] for a in appointments]
    check(CTX["appointment"]["appointment_id"] in ids, "结果未包含本预约，共 %s 条" % len(ids))
    return "HTTP 200，该教练共 %s 条预约，包含 #%s" % (len(ids), CTX["appointment"]["appointment_id"])


@case("APT-06", "预约管理", "按日期查询预约", "P0", "HTTP 200，结果含本预约")
def apt_06():
    appointments, _ = call("GET", "/api/appointments/date/%s" % APT_DATE)
    ids = [a["appointment_id"] for a in appointments]
    check(CTX["appointment"]["appointment_id"] in ids, "%s 共 %s 条，未包含本预约" % (APT_DATE, len(ids)))
    return "HTTP 200，%s 共 %s 条预约，包含 #%s" % (
        APT_DATE, len(ids), CTX["appointment"]["appointment_id"])


@case("APT-07", "预约管理", "确认预约并记录审计", "P0", "状态=已确认，审计出现确认记录")
def apt_07():
    appointment_id = CTX["appointment"]["appointment_id"]
    appointment, _ = call("PUT", "/api/appointments/%s" % appointment_id, {"status": "已确认"})
    check(appointment.get("status") == "已确认", "状态未变更：%s" % appointment.get("status"))
    logs, _ = call("GET", "/api/audit-logs/coach/%s" % CTX["coach"]["coach_id"])
    matched = [l for l in logs
               if l.get("operation_type") == "确认预约课程"
               and str(appointment_id) in str(l.get("operation_result", ""))]
    check(bool(matched), "审计未找到确认记录（共 %s 条日志）" % len(logs))
    CTX["appointment"]["status"] = "已确认"
    return "HTTP 200，状态=已确认，审计记录=%s" % matched[0]["operation_result"]


@case("APT-08", "预约管理", "非法状态校验", "P1", "请求被拒绝，HTTP 400")
def apt_08():
    body = {"student_id": CTX["student_a"]["student_id"], "coach_id": CTX["coach"]["coach_id"],
            "appointment_date": APT_DATE, "start_time": 14, "end_time": 16, "status": "已上课"}
    status, payload, _h, _e = request("POST", "/api/appointments", body)
    check(status == 400, "非法状态期望 HTTP 400，实际 %s（%s）" % (status, _brief(payload)))
    return "HTTP 400，非法状态被拒绝"


@case("APT-09", "预约管理", "非法时段校验", "P1", "请求被拒绝，HTTP 400")
def apt_09():
    body = {"student_id": CTX["student_a"]["student_id"], "coach_id": CTX["coach"]["coach_id"],
            "appointment_date": APT_DATE, "start_time": 25, "end_time": 26, "status": "待确认"}
    status, payload, _h, _e = request("POST", "/api/appointments", body)
    check(status == 400, "非法时段期望 HTTP 400，实际 %s（%s）" % (status, _brief(payload)))
    return "HTTP 400，非法时段被拒绝"


@case("APT-10", "预约管理", "查询不存在预约", "P1", "HTTP 404 且 detail=预约不存在")
def apt_10():
    status, payload, _h, _e = request("GET", "/api/appointments/999999")
    check(status == 404, "期望 HTTP 404，实际 %s" % status)
    check(isinstance(payload, dict) and payload.get("detail") == "预约不存在",
          "detail 不符：%s" % _brief(payload))
    return "HTTP 404，detail=预约不存在"


@case("APT-11", "预约管理", "修改不存在预约", "P1", "HTTP 404 且 detail=预约不存在")
def apt_11():
    status, payload, _h, _e = request("PUT", "/api/appointments/999999", {"status": "已确认"})
    check(status == 404, "期望 HTTP 404，实际 %s" % status)
    check(isinstance(payload, dict) and payload.get("detail") == "预约不存在",
          "detail 不符：%s" % _brief(payload))
    return "HTTP 404，detail=预约不存在"


@case("APT-12", "预约管理", "删除预约", "P1", "删除成功，再次查询 404")
def apt_12():
    appointment = create_appointment(CTX["student_a"]["student_id"],
                                     CTX["coach"]["coach_id"], "2027-01-06", 10, 11)
    payload, _ = call("DELETE", "/api/appointments/%s" % appointment["appointment_id"])
    check(payload.get("message") == "删除成功", "message 不符：%s" % _brief(payload))
    status, _p, _h, _e = request("GET", "/api/appointments/%s" % appointment["appointment_id"])
    check(status == 404, "删除后期望 HTTP 404，实际 %s" % status)
    CLEANUP[:] = [item for item in CLEANUP if item != ("appointment", appointment["appointment_id"])]
    return "HTTP 200 删除成功，复查 HTTP 404"


@case("APT-13", "预约管理", "预约完成扣减课时", "P0", "生成 -2 课时记录，结余=3")
def apt_13():
    student = create_student("课时", driving_years=2)
    CTX["student_apt13"] = student
    create_recharge(student["student_id"], amount=500, course_count=5)
    appointment = create_appointment(student["student_id"],
                                     CTX["coach"]["coach_id"], "2027-01-07", 10, 12)
    updated, _ = call("PUT", "/api/appointments/%s" % appointment["appointment_id"],
                      {"status": "已完成"})
    check(updated.get("status") == "已完成", "状态未变更：%s" % updated.get("status"))
    records = balance_records_of(student["student_id"])
    consumed = [r for r in records if r.get("type") == "课时消耗"]
    check(bool(consumed), "未生成课时消耗记录：%s" % _brief(records))
    record = consumed[0]
    check(record.get("hours") == -2, "课时数不符：%s" % record.get("hours"))
    check(record.get("balance") == 3, "结余不符：期望 3，实际 %s" % record.get("balance"))
    check(record.get("appointment_id") == appointment["appointment_id"], "预约 ID 未关联")
    return "HTTP 200，课时消耗 -2，结余 3，关联预约 #%s" % appointment["appointment_id"]


@case("APT-14", "预约管理", "预约引用不存在学员", "P1", "请求被拒绝（HTTP 400），不产生脏数据")
def apt_14():
    body = {"student_id": 999999, "coach_id": CTX["coach"]["coach_id"],
            "appointment_date": "2027-01-08", "start_time": 10, "end_time": 12, "status": "待确认"}
    status, payload, _h, _e = request("POST", "/api/appointments", body)
    if status == 200 and isinstance(payload, dict):
        remember("appointment", payload.get("appointment_id"))
        raise AssertionError("期望 HTTP 400，实际 200，已生成脏数据 appointment_id=%s"
                             % payload.get("appointment_id"))
    check(status == 400, "期望 HTTP 400，实际 %s" % status)
    return "HTTP 400，非法学员被拒绝"


# ===========================================================================
# 5.7 充值管理 REC
# ===========================================================================
@case("REC-01", "充值管理", "新增充值记录", "P0", "HTTP 200，金额与课时回显一致")
def rec_01():
    student = create_student("充值", driving_years=1)
    CTX["student_rec"] = student
    recharge = create_recharge(student["student_id"], amount=1000, course_count=10)
    CTX["recharge"] = recharge
    check(recharge.get("amount") == 1000, "金额不符：%s" % recharge.get("amount"))
    check(recharge.get("course_count") == 10, "课时不符：%s" % recharge.get("course_count"))
    return "HTTP 200，recharge_id=%s，金额 1000 元，课时 10" % recharge["recharge_id"]


@case("REC-02", "充值管理", "充值自动生成余额记录", "P0", "余额记录：充值 / 10 课时 / 结余 10")
def rec_02():
    recharge_id = CTX["recharge"]["recharge_id"]
    records = balance_records_of(CTX["student_rec"]["student_id"])
    matched = [r for r in records if r.get("recharge_id") == recharge_id]
    check(bool(matched), "未生成关联余额记录：%s" % _brief(records))
    record = matched[0]
    check(record.get("type") == "充值", "类型不符：%s" % record.get("type"))
    check(record.get("hours") == 10, "课时不符：%s" % record.get("hours"))
    check(record.get("balance") == 10, "结余不符：%s" % record.get("balance"))
    return "余额记录生成：type=充值，hours=10，balance=10"


@case("REC-03", "充值管理", "充值列表查询", "P1", "HTTP 200 且包含本次充值")
def rec_03():
    recharges, _ = call("GET", "/api/recharges")
    ids = [r["recharge_id"] for r in recharges]
    check(CTX["recharge"]["recharge_id"] in ids, "列表未包含本次充值")
    return "HTTP 200，共 %s 条充值记录，包含 #%s" % (
        len(ids), CTX["recharge"]["recharge_id"])


@case("REC-04", "充值管理", "修改充值课时并重算余额", "P0", "课时=12，余额记录同步为 12")
def rec_04():
    base = CTX["recharge"]
    body = {"student_id": base["student_id"], "amount": base["amount"],
            "course_count": 12, "recharge_time": base["recharge_time"]}
    recharge, _ = call("PUT", "/api/recharges/%s" % base["recharge_id"], body)
    check(recharge.get("course_count") == 12, "课时未更新：%s" % recharge.get("course_count"))
    records = balance_records_of(base["student_id"])
    matched = [r for r in records if r.get("recharge_id") == base["recharge_id"]]
    check(bool(matched), "余额记录丢失")
    check(matched[0].get("hours") == 12, "余额记录课时未同步：%s" % matched[0].get("hours"))
    check(matched[0].get("balance") == 12, "余额记录结余未重算：%s" % matched[0].get("balance"))
    CTX["recharge"].update(recharge)
    return "HTTP 200，course_count=12，余额记录 hours=12、balance=12"


@case("REC-05", "充值管理", "删除充值并清理余额", "P0", "删除成功，余额记录被清理")
def rec_05():
    recharge_id = CTX["recharge"]["recharge_id"]
    student_id = CTX["recharge"]["student_id"]
    payload, _ = call("DELETE", "/api/recharges/%s" % recharge_id)
    check(payload.get("message") == "删除成功", "message 不符：%s" % _brief(payload))
    records = balance_records_of(student_id)
    check(not records, "余额记录未清理：%s" % _brief(records))
    CLEANUP[:] = [item for item in CLEANUP if item != ("recharge", recharge_id)]
    return "HTTP 200 删除成功，该学员余额记录为空"


@case("REC-06", "充值管理", "查询不存在充值记录", "P2", "HTTP 404（与其他资源错误语义一致）")
def rec_06():
    status, payload, _h, _e = request("GET", "/api/recharges/999999")
    check(status == 404, "期望 HTTP 404，实际 %s（%s）" % (status, _brief(payload)))
    return "HTTP 404，detail=%s" % (payload.get("detail") if isinstance(payload, dict) else "")


# ===========================================================================
# 5.8 余额记录 BAL
# ===========================================================================
@case("BAL-01", "余额记录", "余额记录列表", "P0", "HTTP 200，字段完整")
def bal_01():
    records, _ = call("GET", "/api/balance-records")
    check(isinstance(records, list) and records, "余额记录为空")
    for key in ("record_id", "student_id", "record_date", "hours", "balance", "type"):
        check(key in records[0], "字段缺失：%s" % key)
    return "HTTP 200，共 %s 条余额记录" % len(records)


@case("BAL-02", "余额记录", "按学员查询余额", "P0", "HTTP 200，含充值/消耗记录")
def bal_02():
    student_id = CTX["student_apt13"]["student_id"]
    records = balance_records_of(student_id)
    types = sorted(set(r.get("type") for r in records))
    check(records, "该学员无余额记录")
    check(set(types).issubset({"充值", "课时消耗"}), "类型异常：%s" % types)
    return "HTTP 200，共 %s 条记录，类型=%s" % (len(records), types)


@case("BAL-03", "余额记录", "查询不存在余额记录", "P1", "HTTP 404 且 detail=余额记录不存在")
def bal_03():
    status, payload, _h, _e = request("GET", "/api/balance-records/999999")
    check(status == 404, "期望 HTTP 404，实际 %s" % status)
    check(isinstance(payload, dict) and payload.get("detail") == "余额记录不存在",
          "detail 不符：%s" % _brief(payload))
    return "HTTP 404，detail=余额记录不存在"


# ===========================================================================
# 5.9 操作审计 AUD
# ===========================================================================
@case("AUD-01", "操作审计", "审计日志列表", "P0", "HTTP 200，非空且字段完整")
def aud_01():
    logs, _ = call("GET", "/api/audit-logs/")
    check(isinstance(logs, list) and logs, "审计日志为空")
    for key in ("audit_id", "operator", "operation_time", "operation_type", "operation_result"):
        check(key in logs[0], "字段缺失：%s" % key)
    return "HTTP 200，共 %s 条审计日志" % len(logs)


@case("AUD-02", "操作审计", "按学员查询审计", "P0", "HTTP 200，含创建预约记录")
def aud_02():
    logs = audit_logs_of_student(CTX["student_a"]["student_id"])
    types = [l.get("operation_type") for l in logs]
    check("创建预约课程" in types, "未找到创建预约记录，类型=%s" % types)
    return "HTTP 200，共 %s 条，类型含创建预约课程" % len(logs)


@case("AUD-03", "操作审计", "按教练查询审计", "P0", "HTTP 200，含确认预约记录")
def aud_03():
    logs, _ = call("GET", "/api/audit-logs/coach/%s" % CTX["coach"]["coach_id"])
    types = [l.get("operation_type") for l in logs]
    check("确认预约课程" in types, "未找到确认记录，类型=%s" % types)
    return "HTTP 200，共 %s 条，类型含确认预约课程" % len(logs)


@case("AUD-04", "操作审计", "无记录学员返回 404", "P1", "HTTP 404 且 detail=没有找到该学员的操作记录")
def aud_04():
    # 使用不存在的学员 ID：历史遗留审计数据可能占用被复用的主键，导致误判
    status, payload, _h, _e = request("GET", "/api/audit-logs/student/999999999")
    check(status == 404, "期望 HTTP 404，实际 %s（%s）" % (status, _brief(payload)))
    check(isinstance(payload, dict)
          and payload.get("detail") == "没有找到该学员的操作记录",
          "detail 不符：%s" % _brief(payload))
    return "HTTP 404，detail=没有找到该学员的操作记录"


# ===========================================================================
# 5.10 端到端业务闭环 E2E
# ===========================================================================
@case("E2E-01", "端到端", "充值→预约→确认→完成→余额扣减→审计追溯", "P0",
      "余额 10→8，状态流转正确，审计可追溯")
def e2e_01():
    student = create_student("闭环", driving_years=2, remark="UAT端到端")
    student_id = student["student_id"]
    create_recharge(student_id, amount=1000, course_count=10)
    appointment = create_appointment(student_id, CTX["coach"]["coach_id"], "2027-01-09", 10, 12)
    appointment_id = appointment["appointment_id"]

    confirmed, _ = call("PUT", "/api/appointments/%s" % appointment_id, {"status": "已确认"})
    check(confirmed.get("status") == "已确认", "确认失败：%s" % confirmed.get("status"))
    completed, _ = call("PUT", "/api/appointments/%s" % appointment_id, {"status": "已完成"})
    check(completed.get("status") == "已完成", "完成失败：%s" % completed.get("status"))

    records = balance_records_of(student_id)
    recharge_rows = [r for r in records if r.get("type") == "充值"]
    consume_rows = [r for r in records if r.get("type") == "课时消耗"]
    check(recharge_rows and recharge_rows[0]["balance"] == 10,
          "充值后结余不符：%s" % _brief(recharge_rows))
    check(consume_rows and consume_rows[0]["balance"] == 8,
          "扣减后结余不符：%s" % _brief(consume_rows))

    logs = audit_logs_of_student(student_id)
    types = [l.get("operation_type") for l in logs]
    for expected_type in ("充值", "创建预约课程", "确认预约课程", "标记预约课程为已完成"):
        check(expected_type in types, "审计缺少「%s」，实际=%s" % (expected_type, types))

    return "预约 #%s：待确认→已确认→已完成；课时 10→8；审计覆盖 %s" % (
        appointment_id, types)


# ===========================================================================
# 执行与结果输出
# ===========================================================================
def run_all():
    print("=" * 78)
    print("驾驶智陪工作台 · UAT 验收测试")
    print("API: %s    WEB: %s" % (API, WEB))
    print("开始时间: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 78)

    shots = ScreenshotSession()
    shot_ready = shots.start()
    if not shot_ready:
        print("[WARN] 截图服务不可用：%s" % shots.error)

    results = []
    for item in CASES:
        started = time.time()
        try:
            actual = item.fn()
            status, failure = "PASS", ""
        except Exception as exc:                      # 单条用例失败不阻断后续用例
            actual = str(exc) or exc.__class__.__name__
            status, failure = "FAIL", "%s: %s" % (exc.__class__.__name__, exc)
        elapsed = time.time() - started

        # 用例刚执行完，数据仍在库中，立即截取对应业务页面作为关键步骤证据
        screenshot = None
        if shot_ready:
            url, focus, caption = shot_spec(item)
            screenshot = shots.capture(item.cid, url, focus, item.title, caption, status)

        results.append({
            "id": item.cid, "module": item.module, "title": item.title,
            "priority": item.priority, "expected": item.expected,
            "actual": actual, "status": status, "failure": failure,
            "duration": round(elapsed, 3),
            "screenshot": ("screenshots/%s.jpg" % item.cid if screenshot else ""),
        })
        flag = "PASS" if status == "PASS" else "FAIL"
        print("[%s] %-8s %-28s %6.3fs  %s" % (flag, item.cid, item.title, elapsed,
                                              "" if status == "PASS" else actual))

    shots.stop()
    return results


def summarize(results):
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    p0_failed = sum(1 for r in results if r["status"] == "FAIL" and r["priority"] == "P0")
    return {
        "total": total, "passed": passed, "failed": failed,
        "pass_rate": round(passed * 100.0 / total, 2) if total else 0,
        "p0_failed": p0_failed,
        "duration": round(sum(r["duration"] for r in results), 2),
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "run_id": RUN_ID,
    }


def write_json(results, summary, cleaned):
    data = {"summary": summary, "environment": {"api": API, "web": WEB},
            "cleanup_removed": cleaned, "cases": results}
    (REPORT_DIR / "results.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_junit(results, summary):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<testsuite name="驾驶智陪工作台-UAT" tests="%d" failures="%d" errors="0" time="%.3f" timestamp="%s">'
             % (summary["total"], summary["failed"], summary["duration"],
                datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))]
    for row in results:
        lines.append('  <testcase classname="%s" name="%s %s" time="%.3f">' % (
            html.escape(row["module"]), row["id"], html.escape(row["title"]), row["duration"]))
        if row["status"] == "FAIL":
            lines.append('    <failure message="%s">预期：%s&#10;实际：%s</failure>' % (
                html.escape(row["actual"], quote=True),
                html.escape(row["expected"], quote=True),
                html.escape(row["actual"], quote=True)))
        lines.append('  </testcase>')
    lines.append('</testsuite>')
    (REPORT_DIR / "junit.xml").write_text("\n".join(lines), encoding="utf-8")


def module_stats(results):
    order, stats = [], {}
    for row in results:
        name = row["module"]
        if name not in stats:
            order.append(name)
            stats[name] = {"total": 0, "passed": 0, "failed": 0}
        stats[name]["total"] += 1
        if row["status"] == "PASS":
            stats[name]["passed"] += 1
        else:
            stats[name]["failed"] += 1
    return [(name, stats[name]) for name in order]


# ===========================================================================
# HTML 验收报告
# ===========================================================================
REPORT_CSS = """
* { box-sizing: border-box; }
body { margin: 0; padding: 32px 24px; background: #f5f7fa; color: #1f2937;
  font-family: "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif; }
.wrap { max-width: 1180px; margin: 0 auto; }
.sheet { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 28px 32px; box-shadow: 0 1px 3px rgba(16,24,40,.05); }
.brand { display: flex; align-items: center; gap: 12px; }
.logo { width: 36px; height: 36px; border-radius: 9px; background: #2f54eb; color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; }
h1 { margin: 0; font-size: 22px; letter-spacing: .3px; }
.sub { margin: 4px 0 0; font-size: 13px; color: #6b7280; }
.meta { margin-top: 18px; display: flex; flex-wrap: wrap; gap: 10px 28px; font-size: 12px; color: #6b7280; }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 22px; }
.kpi { border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 16px; background: #fafbff; }
.kpi .label { font-size: 12px; color: #6b7280; }
.kpi .value { margin-top: 6px; font-size: 24px; font-weight: 700; font-variant-numeric: tabular-nums; }
.kpi.pass .value { color: #15803d; }
.kpi.fail .value { color: #b91c1c; }
h2 { margin: 30px 0 10px; font-size: 15px; font-weight: 600; }
.badge { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 12px;
  font-weight: 600; white-space: nowrap; }
.badge.pass { background: #dcfce7; color: #15803d; }
.badge.fail { background: #fee2e2; color: #b91c1c; }
.pri { display: inline-block; padding: 1px 7px; border-radius: 5px; font-size: 11px;
  background: #eef1ff; color: #1e2a78; font-weight: 600; }
.pri.p2 { background: #f3f4f6; color: #6b7280; }
.mono { font-variant-numeric: tabular-nums; color: #6b7280; }
.group { margin-top: 26px; }
.group-title { display: flex; align-items: center; gap: 10px; padding: 8px 12px;
  background: #eef1ff; border-left: 3px solid #2f54eb; border-radius: 6px; font-size: 13px; font-weight: 600; }
.group-title .n { color: #6b7280; font-weight: 400; }
.defect { border: 1px solid #fde2e2; background: #fff8f8; border-radius: 10px;
  padding: 14px 16px; margin-top: 10px; font-size: 13px; }
.defect .title { font-weight: 600; color: #b91c1c; }
.defect p { margin: 6px 0 0; color: #4b5563; }
.note { margin-top: 26px; font-size: 12px; color: #6b7280; line-height: 1.8;
  border-top: 1px dashed #e5e7eb; padding-top: 14px; }
.empty { color: #15803d; font-size: 13px; }
body.dark { background: #111827; color: #e5e7eb; }
body.dark .sheet { background: #1f2937; border-color: #374151; }
body.dark .kpi { background: #111827; border-color: #374151; }
body.dark .group-title { background: #1e2a78; }
body.dark .case, body.dark .module-line { background: #111827; border-color: #374151; }
.mono { font-variant-numeric: tabular-nums; color: #6b7280; }
.module-line { display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  padding: 10px 14px; border: 1px solid #e5e7eb; border-radius: 8px; margin-top: 8px;
  font-size: 13px; background: #fafbff; }
.module-line .name { font-weight: 600; min-width: 96px; }
.module-line .stat { color: #6b7280; font-variant-numeric: tabular-nums; }
.module-line .bar { flex: 1; height: 6px; min-width: 120px; background: #e5e7eb;
  border-radius: 999px; overflow: hidden; }
.module-line .bar i { display: block; height: 100%; background: #2f54eb; }
.case { border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px 18px;
  margin-top: 14px; background: #fff; }
.case-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.case-id { font-weight: 700; color: #1e2a78; font-size: 13px; }
.case-title { font-size: 14px; font-weight: 600; }
.case-time { margin-left: auto; font-size: 12px; color: #9ca3af;
  font-variant-numeric: tabular-nums; }
.case-line { margin: 9px 0 0; font-size: 13px; line-height: 1.75; color: #374151; }
.case-line b { color: #6b7280; font-weight: 600; }
.case-line .real { color: #1f2937; }
.shot-cap { margin: 14px 0 6px; font-size: 12px; color: #6b7280; }
.shot-cap .red { color: #e11d48; font-weight: 600; }
.shot-img { width: 100%; display: block; border: 1px solid #e5e7eb; border-radius: 8px;
  background: #fff; }
.shot-missing { font-size: 12px; color: #9ca3af; }
"""


def _badge(status):
    cls = "pass" if status == "PASS" else "fail"
    text = "通过" if status == "PASS" else "失败"
    return '<span class="badge %s">%s</span>' % (cls, text)


def build_html(results, summary, cleaned):
    esc = html.escape
    modules = module_stats(results)
    failed = [r for r in results if r["status"] == "FAIL"]

    parts = []
    parts.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append('<title>驾驶智陪工作台 · UAT 验收测试报告</title>')
    parts.append('<style>%s</style></head><body><div class="wrap"><div class="sheet">' % REPORT_CSS)

    parts.append('<div class="brand"><div class="logo">智</div><div>')
    parts.append('<h1>驾驶智陪工作台 · UAT 验收测试报告</h1>')
    parts.append('<p class="sub">用户验收测试 · 接口验收 + 端到端业务闭环</p></div></div>')
    parts.append('<div class="meta"><span>执行编号：%s</span><span>执行时间：%s</span>'
                 '<span>后端：%s</span><span>前端：%s</span><span>用例总数：%s 条</span></div>'
                 % (esc(summary["run_id"]), esc(summary["start_time"]),
                    esc(API), esc(WEB), summary["total"]))

    parts.append('<div class="kpis">')
    parts.append('<div class="kpi"><div class="label">用例总数</div><div class="value">%s</div></div>' % summary["total"])
    parts.append('<div class="kpi pass"><div class="label">通过</div><div class="value">%s</div></div>' % summary["passed"])
    parts.append('<div class="kpi fail"><div class="label">失败</div><div class="value">%s</div></div>' % summary["failed"])
    parts.append('<div class="kpi"><div class="label">通过率</div><div class="value">%s%%</div></div>' % summary["pass_rate"])
    parts.append('</div>')

    parts.append('<h2>一、模块执行概览</h2>')
    for name, stat in modules:
        rate = round(stat["passed"] * 100.0 / stat["total"], 1) if stat["total"] else 0
        parts.append('<div class="module-line"><span class="name">%s</span>'
                     '<span class="stat">用例 %s 条 · 通过 %s · 失败 %s · 通过率 %s%%</span>'
                     '<span class="bar"><i style="width:%s%%"></i></span></div>'
                     % (esc(name), stat["total"], stat["passed"], stat["failed"], rate, rate))

    parts.append('<h2>二、缺陷清单</h2>')
    if failed:
        for index, row in enumerate(failed, 1):
            level = {"P0": "高", "P1": "中", "P2": "低"}.get(row["priority"], "低")
            parts.append('<div class="defect"><div class="title">DEF-%02d %s（%s）· 严重程度：%s</div>'
                         '<p>关联用例：%s %s</p><p>预期结果：%s</p><p>实际结果：%s</p>'
                         '<p>处理建议：请研发确认错误语义/数据校验逻辑，修复后回归该用例。</p></div>'
                         % (index, esc(row["title"]), row["id"], level,
                            row["id"], esc(row["title"]), esc(row["expected"]), esc(row["actual"])))
    else:
        parts.append('<p class="empty">本次执行未发现缺陷。</p>')

    parts.append('<h2>三、用例执行明细（含关键步骤截图）</h2>'
                 '<p class="sub" style="margin:0 0 4px">每条用例独立成段：先列出用例信息与预期/实际结果，'
                 '再附该用例执行完成时的真实页面截图。截图中'
                 '<span style="color:#e11d48;font-weight:600">红色边框与「关键数据」标签</span>'
                 '标出与本用例直接相关的数据，点击图片可查看原图。</p>')
    for name, _stat in modules:
        rows = [r for r in results if r["module"] == name]
        passed_n = sum(1 for r in rows if r["status"] == "PASS")
        parts.append('<div class="group"><div class="group-title">%s'
                     '<span class="n">%s 条 · 通过 %s · 失败 %s</span></div>'
                     % (esc(name), len(rows), passed_n, len(rows) - passed_n))
        for row in rows:
            pri_cls = "pri" if row["priority"] != "P2" else "pri p2"
            shot = row.get("screenshot") or ""
            caption = SHOT_CAPTIONS.get(row["id"], "用例执行后的业务页面")
            parts.append('<div class="case"><div class="case-head">'
                         '<span class="case-id">%s</span>'
                         '<span class="case-title">%s</span>'
                         '<span class="%s">%s</span>%s'
                         '<span class="case-time">%.3fs</span></div>'
                         '<p class="case-line"><b>预期：</b>%s</p>'
                         '<p class="case-line"><b>实际：</b><span class="real">%s</span></p>'
                         '<p class="shot-cap">关键步骤截图 · %s</p>'
                         % (row["id"], esc(row["title"]), pri_cls, row["priority"],
                            _badge(row["status"]), row["duration"],
                            esc(row["expected"]), esc(row["actual"]), esc(caption)))
            if shot:
                parts.append('<a href="%s" target="_blank" rel="noopener">'
                             '<img class="shot-img" src="%s" alt="%s %s" loading="lazy"></a>'
                             % (esc(shot), esc(shot), row["id"], esc(row["title"])))
            else:
                parts.append('<p class="shot-missing">未生成截图（截图服务不可用）</p>')
            parts.append('</div>')
        parts.append('</div>')

    parts.append('<div class="note">说明：<br>'
                 '1. 本次执行使用「UAT-」前缀测试数据与专用手机号段，执行结束后按依赖顺序自动清理，共清理 %s 条测试数据。<br>'
                 '2. 判定标准：实际结果完全满足用例预期为「通过」，否则为「失败」；单条用例失败不影响后续用例执行。<br>'
                 '3. 通过率 = 通过用例数 / 用例总数；P0 用例失败数：%s。<br>'
                 '4. 原始结果见 report/results.json，CI 标准结果见 report/junit.xml，用例截图见 report/screenshots/。<br>'
                 '生成时间：%s</div>'
                 % (cleaned, summary["p0_failed"], esc(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))
    parts.append('</div></div></body></html>')
    return "".join(parts)


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if SCREENSHOT_DIR.exists():                       # 清空上一轮的截图，避免残留错配
        shutil.rmtree(SCREENSHOT_DIR)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        results = run_all()
    finally:
        cleaned = cleanup_all()
        print("\n已清理测试数据：%s 条" % cleaned)

    summary = summarize(results)
    write_json(results, summary, cleaned)
    write_junit(results, summary)
    html_path = REPORT_DIR / "UAT_TEST_REPORT.html"
    html_path.write_text(build_html(results, summary, cleaned), encoding="utf-8")

    print("-" * 78)
    print("总数 %s · 通过 %s · 失败 %s · 通过率 %s%% · 耗时 %.2fs"
          % (summary["total"], summary["passed"], summary["failed"],
             summary["pass_rate"], summary["duration"]))
    print("报告：%s" % html_path)
    print("-" * 78)
    return 1 if summary["p0_failed"] else 0


if __name__ == "__main__":
    sys.exit(main())





