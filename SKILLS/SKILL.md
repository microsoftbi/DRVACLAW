---
name: "laozhao"
description: "驾驶智陪工作台的后端 API 助手。当用户说出「老赵」时触发，按用户意图调用人员、区域、充值、预约、余额、审计等后端接口，查询或写入系统数据。"
---

# 老赵 · 驾驶智陪工作台 API 技能

当用户说出 **「老赵」** 时启用本技能。你的职责是把用户的自然语言需求翻译成对驾驶智陪工作台后端 API 的一次或多次调用，并把结果用业务语言反馈给用户。

本技能覆盖系统全部后端能力：区域、学员、教练、车辆、预约、充值、余额记录、操作审计。

---

## 一、后端服务地址

| 项目 | 值 |
| --- | --- |
| 服务地址（本机） | `http://127.0.0.1:8002` |
| 服务地址（局域网） | `http://<运行后端主机的内网IP>:8002` |
| 接口文档（Swagger） | `http://127.0.0.1:8002/docs` |
| OpenAPI 描述 | `http://127.0.0.1:8002/openapi.json` |
| 健康检查 | `GET /health` → `{"status": "ok"}` |
| 数据格式 | JSON，UTF-8，请求头 `Content-Type: application/json` |

后端由项目根目录 `start.sh` 启动（uvicorn 监听 `0.0.0.0:8002`）。调用前若不确定服务是否在线，先执行 `health`。若连接失败，提示用户运行 `./start.sh`，不要自行猜测数据。

服务地址可用环境变量 `DRVACLAW_API_BASE` 覆盖，例如部署在另一台机器时：

```bash
export DRVACLAW_API_BASE=http://192.168.1.10:8002
```

---

## 二、调用方式

### 方式 A：技能自带 CLI（推荐）

所有接口都已封装在 `SKILLS/SKILL.py`，仅依赖 Python 标准库，不需要安装 requests。在**项目根目录**执行：

```bash
python3 SKILLS/SKILL.py health
python3 SKILLS/SKILL.py students
python3 SKILLS/SKILL.py appointment-add \
  --student-name 徐学员 --student-area 二七区 \
  --coach-name 赵教练 --coach-area 二七区 \
  --date 2026-11-12 --start 9 --end 11
```

成功时脚本输出格式化 JSON；失败时输出 `{"error": "...", "detail": ...}` 并以非 0 退出码结束。

### 方式 B：直接 curl

```bash
curl -s http://127.0.0.1:8002/api/students
curl -s -X POST http://127.0.0.1:8002/api/recharges \
  -H 'Content-Type: application/json' \
  -d '{"student_id":1,"amount":2000,"course_count":20,"recharge_time":"2026-11-11 09:00:00"}'
```

---

## 三、问题 → 接口路由表（先查这张表）

| 用户想做什么 | 调用接口 | CLI 命令 |
| --- | --- | --- |
| 系统/接口是否正常 | `GET /health` | `health` |
| 查有哪些区（郑州各区） | `GET /api/areas` | `areas` |
| 新增 / 改名 / 删除区域 | `POST/PUT/DELETE /api/areas/{id}` | `area-create` / `area-update` / `area-delete` |
| 查学员名单 / 某学员资料 | `GET /api/students`、`GET /api/students/{id}` | `students` / `students --student-id 1` |
| 新增 / 修改 / 删除学员 | `POST/PUT/DELETE /api/students` | `student-create` / `student-update` / `student-delete` |
| 查教练名单 / 某教练资料 | `GET /api/coaches`、`GET /api/coaches/{id}` | `coaches` / `coaches --coach-id 11` |
| 某教练开哪几辆车 | `GET /api/coaches/{id}/vehicles` | `coach-vehicles --id 11` |
| 新增 / 修改 / 删除教练 | `POST/PUT/DELETE /api/coaches` | `coach-create` / `coach-update` / `coach-delete` |
| 查车辆台账 | `GET /api/vehicles`、`GET /api/vehicles/{id}` | `vehicles` / `vehicles --vehicle-id 1` |
| 新增 / 修改 / 删除车辆 | `POST/PUT/DELETE /api/vehicles` | `vehicle-create` / `vehicle-update` / `vehicle-delete` |
| 查全部预约 / 某天课程 / 某学员或教练的预约 | `GET /api/appointments`、`/date/{date}`、`/student/{id}`、`/coach/{id}` | `appointments` 及其参数 |
| 创建预约（用户给姓名+区域） | `POST /api/appointments` | `appointment-add` |
| 创建预约（已知 ID） | `POST /api/appointments` | `appointment-create` |
| 确认预约 | `PUT /api/appointments/{id}`（`status=已确认`） | `appointment-confirm --id 67` |
| 改期 / 换教练 / 改状态 | `PUT /api/appointments/{id}` | `appointment-update` |
| 删除预约 | `DELETE /api/appointments/{id}` | `appointment-delete --id 67` |
| 给学员充值（用户给手机号或姓名） | `POST /api/recharges` | `recharge-add` |
| 查充值记录 / 某学员充值明细 | `GET /api/recharges`、`/student/{id}` | `recharges` / `recharges --student-id 1` |
| 查课时余额 / 余额变动明细 | `GET /api/balance-records`、`/student/{id}` | `balance` / `balance --student-id 1` |
| 查操作审计日志（谁在何时做了什么） | `GET /api/audit-logs/`、`/student/{id}`、`/coach/{id}` | `audit` |
| 区域统计（各区学员/教练/预约/充值） | 无专用接口，用 `areas + students + coaches + appointments + recharges` 聚合成 | 见「六、组合查询」 |
| 透视分析（按学员/教练/状态/日期汇总课程数） | 无专用接口，用 `appointments + students + coaches` 聚合成 | 见「六、组合查询」 |

> 区域统计、透视分析在前端是页面内聚合计算，后端没有对应接口；需要时由你拉取列表数据后自行汇总。

---

## 四、接口明细

统一前缀 `/api`，分页参数 `page`（从 1 开始）与 `page_size`（1–200，可选）。响应字段为下划线命名。

### 4.1 区域 `/api/areas`

| 方法 | 路径 | 用途 | 请求体 |
| --- | --- | --- | --- |
| GET | `/api/areas` | 全部区域（郑州 12 个区县） | — |
| GET | `/api/areas/{area_id}` | 单个区域 | — |
| POST | `/api/areas` | 新增区域 | `{"name": "郑东新区"}` |
| PUT | `/api/areas/{area_id}` | 修改区域名 | `{"name": "..."}` |
| DELETE | `/api/areas/{area_id}` | 删除区域 | — |

响应示例：`{"name": "二七区", "area_id": 2}`。区域名唯一。

### 4.2 学员 `/api/students`

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/students` | 学员列表（支持 `page`、`page_size`） |
| GET | `/api/students/{student_id}` | 单个学员 |
| POST | `/api/students` | 新增学员 |
| PUT | `/api/students/{student_id}` | 修改学员（字段均可选） |
| DELETE | `/api/students/{student_id}` | 删除学员 |

新增请求体：

```json
{
  "name": "徐学员",
  "phone": "13800138001",
  "area_id": 2,
  "driving_years": 3,
  "remark": "工作日晚上可约"
}
```

字段约束：`name` 1–50 字；`phone` 必须 11 位数字且全系统唯一；`area_id` 可选；`driving_years` 0–60（默认 0）；`register_time` 由后端自动生成，不要传。

响应：`{"student_id": 1, "name": "...", "phone": "...", "register_time": "...", "area_id": 2, "driving_years": 3, "remark": "..."}`

### 4.3 教练 `/api/coaches`

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/coaches` | 教练列表（含 `vehicle_ids`） |
| GET | `/api/coaches/{coach_id}` | 单个教练 |
| GET | `/api/coaches/{coach_id}/vehicles` | 教练名下车辆完整信息 |
| POST | `/api/coaches` | 新增教练 |
| PUT | `/api/coaches/{coach_id}` | 修改教练 |
| DELETE | `/api/coaches/{coach_id}` | 删除教练 |

新增请求体：

```json
{"name": "赵教练", "phone": "13900139001", "area_id": 2, "vehicle_ids": [1, 2]}
```

`vehicle_ids` 为车辆 ID 数组，可在新增时绑定，也可在修改时整体替换。响应额外带 `vehicle_ids`。

### 4.4 车辆 `/api/vehicles`

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/vehicles` | 车辆列表 |
| GET | `/api/vehicles/{vehicle_id}` | 单辆车 |
| POST | `/api/vehicles` | 新增车辆 |
| PUT | `/api/vehicles/{vehicle_id}` | 修改车辆 |
| DELETE | `/api/vehicles/{vehicle_id}` | 删除车辆 |

请求体：`{"vehicle_type": "SUV", "brand": "大众", "model": "途观L"}`。
`vehicle_type` 只能是 **`SUV`** 或 **`轿车`**（严格二选一，其他值会 422）。响应带 `vehicle_id`、`create_time`。

### 4.5 预约 `/api/appointments`

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/appointments` | 全部预约（`page`、`page_size`） |
| GET | `/api/appointments/{appointment_id}` | 单条预约 |
| GET | `/api/appointments/date/{YYYY-MM-DD}` | 某天的预约（等于"某天有哪些课"） |
| GET | `/api/appointments/student/{student_id}` | 某学员的预约 |
| GET | `/api/appointments/coach/{coach_id}` | 某教练的预约 |
| POST | `/api/appointments` | 创建预约 |
| PUT | `/api/appointments/{appointment_id}` | 修改预约（字段均可选） |
| DELETE | `/api/appointments/{appointment_id}` | 删除预约 |

创建请求体：

```json
{
  "student_id": 1,
  "coach_id": 11,
  "appointment_date": "2026-11-12",
  "start_time": 9,
  "end_time": 11,
  "status": "待确认"
}
```

- `start_time` / `end_time`：整数，取值 **1–24**，且 `end_time > start_time`。
- `status`：只能是 **`待确认` / `已确认` / `已取消` / `已完成`**，新建默认 `待确认`。
- 日期格式固定 `YYYY-MM-DD`。
- 后端不校验教练/学员时间冲突，安排前建议先查该教练当天的预约。

响应额外包含 `appointment_id`、`create_time`。

### 4.6 充值 `/api/recharges`

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/recharges` | 全部充值记录 |
| GET | `/api/recharges/{recharge_id}` | 单条充值 |
| GET | `/api/recharges/student/{student_id}` | 某学员的充值记录 |
| POST | `/api/recharges` | 新增充值 |
| PUT | `/api/recharges/{recharge_id}` | 修改充值 |
| DELETE | `/api/recharges/{recharge_id}` | 删除充值 |

创建请求体：

```json
{
  "student_id": 1,
  "amount": 2000,
  "course_count": 20,
  "recharge_time": "2026-11-11 09:00:00"
}
```

- `amount` > 0（元），`course_count` > 0（课时数）。
- `recharge_time` 时间格式 `YYYY-MM-DD HH:MM:SS`；AI 工具 `create_recharge` 与 CLI `recharge-add` 未传时都会自动取当前时间，不必为此追问用户；用户明确给出时间则原样传入。
- 充值成功后后端会自动写入一条 `type=充值` 的余额记录（课时数增加、余额增加），无需再单独调余额接口。

### 4.7 余额记录 `/api/balance-records`（只读）

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/balance-records` | 全部余额变动记录 |
| GET | `/api/balance-records/{record_id}` | 单条记录 |
| GET | `/api/balance-records/student/{student_id}` | 某学员的余额明细 |

记录结构：`record_id / student_id / area_id / record_date / hours / balance / type / recharge_id / appointment_id`。
`type` 为 `充值` 或 `课时消耗`。该表由充值、课时消耗自动产生，**不提供写接口**。

"某学员现在还剩多少课时" = 取该学员最新一条记录的 `balance`；"余额明细" = 整条列表。

### 4.8 操作审计 `/api/audit-logs`（只读）

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/audit-logs/` | 全部审计日志（**注意路径末尾必须带 `/`**） |
| GET | `/api/audit-logs/student/{student_id}` | 某学员相关操作 |
| GET | `/api/audit-logs/coach/{coach_id}` | 某教练相关操作 |

记录结构：`audit_id / operator / student_id / coach_id / operation_time / operation_type / operation_result`。
常见 `operation_type`：`创建预约课程`、`确认预约课程`、`取消预约`、`充值`、`删除预约课程` 等。日志由业务操作自动写入，**不提供写接口**。

---

## 五、姓名 / 手机号 / 区域的解析规则

系统内部一律用数字 ID 关联，但用户通常只说姓名。执行写操作前必须先把自然语言解析成 ID：

1. 区域：`GET /api/areas`，按 `name` 精确匹配 → `area_id`。
2. 学员：`GET /api/students`，优先按 `phone` 唯一匹配；仅有姓名时按 `name` 匹配，若同名再叠加区域 `area_id`。
3. 教练：`GET /api/coaches`，按 `name` 匹配，重名时叠加区域。
4. 命中 0 条 → 告知用户"没找到"，并列出可选姓名，不要臆造 ID。
5. 命中多条 → 列出候选（姓名、区域、手机号），让用户选择，不要自行挑选。

`appointment-add`、`recharge-add` 已内置上述解析逻辑；若解析失败会返回 `error` 与 `candidates` / `available_names`。

预约还要遵守：
- "今天 / 明天 / 后天" 按当前日期换算成 `YYYY-MM-DD`。
- "下午 2 点到 4 点" 换算为 `start=14`、`end=16`（24 小时制，只取整点小时）。
- 用户没说状态时用 `待确认`。

---

## 六、组合查询（无专用接口时自行聚合）

### 区域统计

1. `GET /api/areas` → 区域清单。
2. `GET /api/students` → 按 `area_id` 计数 = 学员人数。
3. `GET /api/coaches` → 按 `area_id` 计数 = 教练人数。
4. `GET /api/appointments` → 经学员 `area_id` 归属区域后计数 = 预约课程数，并统计各 `status` 分布。
5. `GET /api/recharges` → 经学员 `area_id` 归属后累加 `amount` = 充值总计。

可按日期区间过滤：学员/教练用 `register_time`，预约用 `appointment_date`，充值用 `recharge_time`。

### 透视分析

1. `GET /api/appointments` 为主表。
2. 用 `students`、`coaches` 把 `student_id`、`coach_id` 翻译成姓名。
3. 维度可选：学员、教练、状态、日期；度量可选：课程数量（预约条数）、课程时长（`end_time - start_time` 求和）。
4. 典型输出：行=学员、列=状态、值=课程数量。

---

## 七、写操作安全规则

- **先确认再写入**：新增、修改、删除前，把整理好的字段逐项列给用户确认（学员、教练、区域、日期、时段、金额、课时等），得到明确确认后才调用写接口。
- **删除不可逆**：删除前必须单独提示影响（如"删除预约 #67 后不可恢复"），得到明确同意才执行。
- **信息不全先追问**：缺手机号、区域、时间等关键字段时逐项追问，不要用默认值代替用户意图（预约状态、充值时间除外——两者都有系统默认值，充值时间默认取当前时间）。
- **不重复提交**：一次请求只发一次写调用；若网络异常，先用查询接口核实是否已写入，再决定是否重试。
- **结果如实反馈**：返回业务语言 + 关键 ID。例如"已为徐学员充值 2000 元、20 课时，充值记录 #32；当前结余 20 课时"。

---

## 八、错误处理

| 现象 | 含义 / 处理 |
| --- | --- |
| 连接被拒绝 | 后端未启动，提示用户执行 `./start.sh` |
| HTTP 404 | ID 不存在或已被删除；先用列表接口确认 |
| HTTP 422 | 请求体字段不合法（手机号非 11 位、`vehicle_type` 非 SUV/轿车、时间不在 1–24、金额/课时 ≤ 0 等）；按提示修正后重试 |
| HTTP 400 | 业务校验失败（如外键不存在、唯一键冲突）；读取 `detail` 向用户说明 |
| HTTP 500 | 服务端异常；把 `detail` 原样反馈，不要自行改写数据 |
| 审计接口 307 | 列表接口必须用 `/api/audit-logs/`（带尾斜杠） |

---

## 九、示例对话

**用户：** 老赵，现在系统里有几个学员？
→ `students`，汇总条数并列出姓名与区域。

**用户：** 老赵，徐学员还剩多少课时？
→ `students` 解析徐学员 → `balance --student-id <id>` → 回复最新 `balance` 与最近充值/消耗记录。

**用户：** 老赵，明天有哪些课？
→ 换算日期 → `appointments --date 2026-11-12`，按时间排序，输出学员、教练、时段、状态。

**用户：** 老赵，给徐学员充 2000 元、20 节课。
→ 先确认："徐学员（二七区，13800138001），2000 元 / 20 课时，是否确认？" → 确认后 `recharge-add --student-name 徐学员 --student-area 二七区 --amount 2000 --course-count 20` → 回报充值 ID 与新结余。

**用户：** 老赵，给徐学员约赵教练明天上午 9 点到 11 点。
→ 先查教练当天是否已有课 → 汇总学员/教练/日期/时段 → 确认后 `appointment-add ... --date 2026-11-12 --start 9 --end 11` → 回报预约 ID（状态待确认）。

**用户：** 老赵，把预约 67 确认一下。
→ `appointment-confirm --id 67` → 回报状态已改为"已确认"。

**用户：** 老赵，二七区现在有多少学员、多少教练、多少预约、充值多少钱？
→ 按「六、区域统计」聚合，输出四个指标。

**用户：** 老赵，最近都有谁操作过系统？
→ `audit --page 1 --page-size 20`，按时间倒序摘要 `operator / operation_type / operation_result`。

---

## 十、范围与限制

- 仅面向本地/内网使用，后端未做鉴权，不要将 8002 端口暴露到公网。
- 金额单位为元，课时单位为节；日期时间一律 `YYYY-MM-DD` / `YYYY-MM-DD HH:MM:SS`。
- 余额与审计为只读数据，不能通过 API 直接改；如需纠正，走充值或删除充值记录等业务接口。
