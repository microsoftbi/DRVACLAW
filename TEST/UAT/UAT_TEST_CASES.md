# 驾驶智陪工作台 · UAT 验收测试用例

| 项目 | 内容 |
| --- | --- |
| 被测系统 | 驾驶智陪工作台（DRVACLAW） |
| 版本 | v1.0 |
| 编写日期 | 2026-11-11 |
| 测试类型 | 用户验收测试（UAT） |
| 测试层级 | 接口验收 + 核心业务闭环 + 页面可达性 |
| 用例总数 | 62 条 |
| 执行方式 | 自动化脚本 `uat_test_suite.py` |

---

## 1. 测试目标

验证「驾驶智陪工作台」在验收环境下的核心业务能力是否满足交付要求，覆盖：

1. 系统环境可用性（后端 API、前端页面、接口文档、跨域访问）。
2. 基础资料维护：区域、学员（含驾龄/备注）、车辆、教练（含车辆关联）。
3. 预约业务：创建、查询、确认、取消、完成、删除，以及状态流转引发的课时扣减。
4. 充值业务：充值记录、余额记录自动生成、课时修改后的余额重算、删除后的余额清理。
5. 数据查询：余额记录、操作审计日志（按学员 / 按教练）。
6. 端到端业务闭环：建档 → 充值 → 预约 → 确认 → 完成 → 余额扣减 → 审计可追溯。

## 2. 测试范围与不在范围内事项

| 范围 | 说明 |
| --- | --- |
| 范围内 | 上述 6 类业务功能的接口行为、数据一致性、状态流转、异常分支、页面可达性 |
| 不在范围内 | 并发压力测试、安全渗透测试、多浏览器兼容性矩阵、移动端适配、第三方支付 |
| 已知限制 | 演示环境数据为测试数据；脚本仅使用「UAT-」前缀数据并在执行后自动清理 |

## 3. 测试环境与数据准备

| 项 | 值 |
| --- | --- |
| 后端服务 | FastAPI + uvicorn，`http://127.0.0.1:8002` |
| 前端服务 | Vue3 + Vite，`http://127.0.0.1:5174` |
| 数据库 | SQLite（`Backend/drvaclaw.db`） |
| 运行环境 | macOS，Python 3.9.6（使用 Backend/.venv，仅依赖标准库） |

**测试数据策略：**

- 新建数据统一使用 `UAT-` 前缀（区域、学员、教练、车辆型号）与专用手机号段（`139` 开头 11 位随机号），避免污染既有演示数据。
- 用例执行结束后，脚本按「预约 → 充值 → 教练 → 车辆 → 学员 → 区域」顺序自动清理本次创建的数据。
- 断言不依赖固定主键，按本次创建返回的 ID 进行校验。

## 4. 用例执行顺序

用例按模块顺序串行执行，后置用例复用前置用例创建的数据（同一脚本生命周期内有效）：

`ENV（环境）→ AREA（区域）→ VEH（车辆）→ STU（学员）→ COA（教练）→ APT（预约）→ REC（充值）→ BAL（余额）→ AUD（审计）→ E2E（端到端）`

---

## 5. 详细测试用例

### 5.1 环境可达性（ENV，5 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| ENV-01 | P0 | 接口 | 后端欢迎接口 | 后端已启动 | ① GET `/` | HTTP 200；`message` =「欢迎使用驾驶智陪工作台 API」 |
| ENV-02 | P0 | 接口 | 健康检查 | 后端已启动 | ① GET `/health` | HTTP 200；`status` = `ok` |
| ENV-03 | P0 | 页面 | 前端页面可访问 | 前端已启动 | ① GET `http://127.0.0.1:5174/` | HTTP 200；页面 `<title>` =「驾驶智陪工作台」 |
| ENV-04 | P1 | 接口 | API 文档可访问 | 后端已启动 | ① GET `/docs` | HTTP 200；页面包含 Swagger UI 标识 |
| ENV-05 | P1 | 接口 | 跨域预检 | 后端已启动 | ① OPTIONS `/api/students`，携带 `Origin` 与 `Access-Control-Request-Method: GET` | HTTP 200；响应头包含 `Access-Control-Allow-Origin` |

### 5.2 区域管理（AREA，7 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| AREA-01 | P0 | 接口 | 区域列表查询 | 后端已启动 | ① GET `/api/areas` | HTTP 200；返回数组且数量 ≥ 10；每条含 `area_id`、`name` |
| AREA-02 | P0 | 接口 | 新增区域 | — | ① POST `/api/areas`，`name`=`UAT区域-<时间戳>` | HTTP 200；返回新 `area_id`；`name` 与入参一致 |
| AREA-03 | P0 | 接口 | 区域详情查询 | AREA-02 已执行 | ① GET `/api/areas/{id}` | HTTP 200；`area_id`、`name` 与新建数据一致 |
| AREA-04 | P1 | 接口 | 区域重命名 | AREA-02 已执行 | ① PUT `/api/areas/{id}`，`name`=`UAT区域-已更新` | HTTP 200；`name` 已更新为新名称 |
| AREA-05 | P1 | 接口 | 区域名称唯一性 | AREA-02 已执行 | ① 使用与 AREA-02 相同的名称再次 POST `/api/areas` | 请求被拒绝，HTTP 400（名称唯一约束生效） |
| AREA-06 | P1 | 接口 | 查询不存在区域 | — | ① GET `/api/areas/999999` | HTTP 404；`detail` =「区域不存在」 |
| AREA-07 | P1 | 接口 | 删除区域 | AREA-02 已执行 | ① DELETE `/api/areas/{id}`；② 再次 GET 该区域 | ① HTTP 200，`message` =「删除成功」；② HTTP 404 |

### 5.3 车辆管理（VEH，7 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| VEH-01 | P0 | 接口 | 车辆列表与车型合法性 | 已有车辆数据 | ① GET `/api/vehicles` | HTTP 200；数量 ≥ 10；所有 `vehicle_type` ∈ {SUV, 轿车}；含 `brand`、`model` |
| VEH-02 | P0 | 接口 | 新增 SUV 车辆 | — | ① POST `/api/vehicles`，`{vehicle_type: SUV, brand: UAT-品牌, model: UAT-型号A}` | HTTP 200；返回 `vehicle_id`；字段回显一致 |
| VEH-03 | P0 | 接口 | 新增轿车 | — | ① POST `/api/vehicles`，`vehicle_type`=`轿车` | HTTP 200；返回 `vehicle_id`；`vehicle_type` = 轿车 |
| VEH-04 | P1 | 接口 | 非法车型校验 | — | ① POST `/api/vehicles`，`vehicle_type`=`跑车` | 请求被拒绝（HTTP 422 或 400），不得落库 |
| VEH-05 | P1 | 接口 | 修改车辆型号 | VEH-02 已执行 | ① PUT `/api/vehicles/{id}`，`model`=`UAT-型号A-改` | HTTP 200；`model` 已更新 |
| VEH-06 | P1 | 接口 | 查询不存在车辆 | — | ① GET `/api/vehicles/999999` | HTTP 404；`detail` =「车辆不存在」 |
| VEH-07 | P1 | 接口 | 删除车辆 | — | ① 新建临时车辆；② DELETE 该车；③ 再次 GET | ① HTTP 200；② `message` =「删除成功」；③ HTTP 404 |

### 5.4 学员管理（STU，7 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| STU-01 | P0 | 接口 | 学员列表 | 已有学员数据 | ① GET `/api/students` | HTTP 200；数量 ≥ 10；每条含 `student_id`、`name`、`phone`、`driving_years`、`remark`、`register_time` |
| STU-02 | P0 | 接口 | 新增学员（驾龄/备注） | 区域可用 | ① POST `/api/students`，`{name: UAT学员A, phone: 139xxxxxxxx, area_id: 已有区域, driving_years: 3, remark: UAT自动化测试学员}` | HTTP 200；返回 `student_id`；`driving_years`=3、`remark` 回显；`register_time` 自动生成 |
| STU-03 | P0 | 接口 | 学员详情 | STU-02 已执行 | ① GET `/api/students/{id}` | HTTP 200；姓名、手机号、区域、驾龄、备注与新建一致 |
| STU-04 | P1 | 接口 | 修改驾龄与备注 | STU-02 已执行 | ① PUT `/api/students/{id}`，`driving_years`=5，`remark`=`UAT备注更新` | HTTP 200；`driving_years`=5、`remark` 已更新；其余字段不变 |
| STU-05 | P1 | 接口 | 手机号唯一性 | STU-02 已执行 | ① 使用 STU-02 的手机号再次 POST `/api/students` | 请求被拒绝，HTTP 400（手机号唯一约束生效） |
| STU-06 | P1 | 接口 | 查询不存在学员 | — | ① GET `/api/students/999999` | HTTP 404；`detail` =「学员不存在」 |
| STU-07 | P1 | 接口 | 删除学员 | — | ① 新建临时学员；② DELETE；③ 再次 GET | ① HTTP 200；② `message` =「删除成功」；③ HTTP 404 |

### 5.5 教练管理（COA，8 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| COA-01 | P0 | 接口 | 教练列表含车辆关联 | 已有教练数据 | ① GET `/api/coaches` | HTTP 200；数量 ≥ 5；每条含 `vehicle_ids`（数组），字段可解析 |
| COA-02 | P0 | 接口 | 新增教练并关联两辆车 | VEH-02、VEH-03 已执行 | ① POST `/api/coaches`，`{name: UAT教练A, phone: 139xxxxxxxx, area_id: 已有区域, vehicle_ids: [车1, 车2]}` | HTTP 200；返回 `coach_id`；`vehicle_ids` 同时包含两辆车 |
| COA-03 | P0 | 接口 | 教练详情含车辆 | COA-02 已执行 | ① GET `/api/coaches/{id}` | HTTP 200；`vehicle_ids` 与创建时一致 |
| COA-04 | P0 | 接口 | 教练车辆明细 | COA-02 已执行 | ① GET `/api/coaches/{id}/vehicles` | HTTP 200；返回 2 条车辆，`vehicle_id` 与关联一致，含车型/品牌/型号 |
| COA-05 | P1 | 接口 | 调整车辆关联 | COA-02 已执行 | ① PUT `/api/coaches/{id}`，`vehicle_ids` 仅保留第二辆车；② 再次 GET 教练 | ① HTTP 200；② `vehicle_ids` 仅包含第二辆车（原关联被替换） |
| COA-06 | P1 | 接口 | 教练手机号唯一性 | COA-02 已执行 | ① 使用 COA-02 的手机号再次 POST `/api/coaches` | 请求被拒绝，HTTP 400（手机号唯一约束生效） |
| COA-07 | P1 | 接口 | 查询不存在教练 | — | ① GET `/api/coaches/999999` | HTTP 404；`detail` =「教练不存在」 |
| COA-08 | P1 | 接口 | 删除教练 | — | ① 新建临时教练；② DELETE；③ 再次 GET | ① HTTP 200；② `message` =「删除成功」；③ HTTP 404 |

### 5.6 预约管理（APT，14 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| APT-01 | P0 | 接口 | 预约列表 | 已有预约数据 | ① GET `/api/appointments` | HTTP 200；数量 ≥ 30；每条含 `appointment_id`、`student_id`、`coach_id`、日期、时段、`status`、`create_time` |
| APT-02 | P0 | 接口 | 创建待确认预约 | STU-02、COA-02 已执行 | ① POST `/api/appointments`，`{student_id, coach_id, appointment_date: 2027-01-05, start_time: 10, end_time: 12, status: 待确认}` | HTTP 200；返回 `appointment_id`；字段回显一致；`create_time` 自动生成；`status`=待确认 |
| APT-03 | P0 | 接口 | 预约详情 | APT-02 已执行 | ① GET `/api/appointments/{id}` | HTTP 200；与创建数据一致 |
| APT-04 | P0 | 接口 | 按学员查询预约 | APT-02 已执行 | ① GET `/api/appointments/student/{student_id}` | HTTP 200；结果中包含 APT-02 的 `appointment_id` |
| APT-05 | P0 | 接口 | 按教练查询预约 | APT-02 已执行 | ① GET `/api/appointments/coach/{coach_id}` | HTTP 200；结果中包含 APT-02 的 `appointment_id` |
| APT-06 | P0 | 接口 | 按日期查询预约 | APT-02 已执行 | ① GET `/api/appointments/date/2027-01-05` | HTTP 200；结果中包含 APT-02 的 `appointment_id` |
| APT-07 | P0 | 接口 | 确认预约并记录审计 | APT-02 已执行 | ① PUT `/api/appointments/{id}`，`status`=已确认；② GET `/api/audit-logs/coach/{coach_id}` | ① HTTP 200 且状态=已确认；② 审计中出现 `确认预约课程` 且包含该预约 ID |
| APT-08 | P1 | 接口 | 非法状态校验 | — | ① POST `/api/appointments`，`status`=`已上课` | 请求被拒绝，HTTP 400（状态取值受约束） |
| APT-09 | P1 | 接口 | 非法时段校验 | — | ① POST `/api/appointments`，`start_time`=25 | 请求被拒绝，HTTP 400（时段取值 1–24） |
| APT-10 | P1 | 接口 | 查询不存在预约 | — | ① GET `/api/appointments/999999` | HTTP 404；`detail` =「预约不存在」 |
| APT-11 | P1 | 接口 | 修改不存在预约 | — | ① PUT `/api/appointments/999999`，`status`=已确认 | HTTP 404；`detail` =「预约不存在」 |
| APT-12 | P1 | 接口 | 删除预约 | — | ① 新建临时预约；② DELETE；③ 再次 GET | ① HTTP 200；② `message` =「删除成功」；③ HTTP 404 |
| APT-13 | P0 | 接口 | 预约完成扣减课时 | 新建学员并充值 5 课时 | ① 创建 10:00–12:00 预约；② PUT 状态=已完成；③ GET `/api/balance-records/student/{id}` | ② HTTP 200 且状态=已完成；③ 新增一条 `课时消耗` 记录：`hours`=-2，`balance`=3，`appointment_id` 对应本预约 |
| APT-14 | P1 | 接口 | 预约引用不存在学员 | — | ① POST `/api/appointments`，`student_id`=999999 | 请求被拒绝（HTTP 400），不得产生脏数据 |

### 5.7 充值管理（REC，6 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| REC-01 | P0 | 接口 | 新增充值记录 | 新建学员（0 课时） | ① POST `/api/recharges`，`{student_id, amount: 1000, course_count: 10, recharge_time: 2027-01-05 09:00:00}` | HTTP 200；返回 `recharge_id`；金额、课时回显一致 |
| REC-02 | P0 | 接口 | 充值自动生成余额记录 | REC-01 已执行 | ① GET `/api/balance-records/student/{id}` | HTTP 200；存在 `type`=充值、`hours`=10、`balance`=10、`recharge_id`=REC-01 的记录 |
| REC-03 | P1 | 接口 | 充值列表查询 | REC-01 已执行 | ① GET `/api/recharges` | HTTP 200；列表包含 REC-01 的 `recharge_id` |
| REC-04 | P0 | 接口 | 修改充值课时并重算余额 | REC-01 已执行 | ① PUT `/api/recharges/{id}`，`course_count`=12；② GET 余额记录 | ① HTTP 200 且课时=12；② 关联余额记录 `hours`=12、`balance`=12 |
| REC-05 | P0 | 接口 | 删除充值并清理余额 | REC-04 已执行 | ① DELETE `/api/recharges/{id}`；② GET `/api/balance-records/student/{id}` | ① HTTP 200；② 关联余额记录已被删除，余额记录为空 |
| REC-06 | P2 | 接口 | 查询不存在充值记录 | — | ① GET `/api/recharges/999999` | HTTP 404（与预约/学员等资源保持一致的错误语义） |

### 5.8 余额记录（BAL，3 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| BAL-01 | P0 | 接口 | 余额记录列表 | APT-13 已执行 | ① GET `/api/balance-records` | HTTP 200；返回数组；记录含 `record_id`、`student_id`、`record_date`、`hours`、`balance`、`type` |
| BAL-02 | P0 | 接口 | 按学员查询余额 | APT-13 已执行 | ① GET `/api/balance-records/student/{id}` | HTTP 200；包含该学员的充值/课时消耗记录，`type` ∈ {充值, 课时消耗} |
| BAL-03 | P1 | 接口 | 查询不存在余额记录 | — | ① GET `/api/balance-records/999999` | HTTP 404；`detail` =「余额记录不存在」 |

### 5.9 操作审计（AUD，4 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| AUD-01 | P0 | 接口 | 审计日志列表 | 已有操作 | ① GET `/api/audit-logs/` | HTTP 200；返回非空数组；含 `audit_id`、`operator`、`operation_time`、`operation_type`、`operation_result` |
| AUD-02 | P0 | 接口 | 按学员查询审计 | STU-02、APT-02 已执行 | ① GET `/api/audit-logs/student/{student_id}` | HTTP 200；非空；包含「创建预约课程」类记录 |
| AUD-03 | P0 | 接口 | 按教练查询审计 | COA-02、APT-02 已执行 | ① GET `/api/audit-logs/coach/{coach_id}` | HTTP 200；非空；包含预约相关操作记录 |
| AUD-04 | P1 | 接口 | 无记录学员返回 404 | 不存在的学员 ID（999999999） | ① GET `/api/audit-logs/student/999999999` | HTTP 404；`detail` =「没有找到该学员的操作记录」 |

### 5.10 端到端业务闭环（E2E，1 条）

| 用例ID | 优先级 | 类型 | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- | --- |
| E2E-01 | P0 | 端到端 | 充值→预约→确认→完成→余额扣减→审计追溯 | 后端可用，存在可用区域/教练/车辆 | ① 新建学员；② 充值 1000 元 / 10 课时；③ 创建 2 小时预约（待确认）；④ 确认预约；⑤ 标记已完成；⑥ 查询余额记录；⑦ 查询学员审计；⑧ 清理数据 | ② 余额记录=10；③ 预约创建成功；④ 状态=已确认；⑤ 状态=已完成；⑥ 新增 -2 课时记录且结余=8；⑦ 审计可查到充值、确认、标记完成记录；⑧ 清理成功 |

---

## 6. 需求追溯矩阵

| 需求编号 | 需求描述 | 覆盖用例 | 用例数 |
| --- | --- | --- | --- |
| FR-01 | 系统环境可用（API / 页面 / 文档 / 跨域） | ENV-01 ~ ENV-05 | 5 |
| FR-02 | 区域基础资料维护 | AREA-01 ~ AREA-07 | 7 |
| FR-03 | 车辆基础资料维护（SUV / 轿车） | VEH-01 ~ VEH-07 | 7 |
| FR-04 | 学员档案维护（驾龄、备注） | STU-01 ~ STU-07 | 7 |
| FR-05 | 教练档案维护及车辆多对多关联 | COA-01 ~ COA-08 | 8 |
| FR-06 | 预约全生命周期管理 | APT-01 ~ APT-12、APT-14 | 13 |
| FR-07 | 预约完成自动扣减课时 | APT-13、E2E-01 | 2 |
| FR-08 | 充值登记与余额自动记账 | REC-01 ~ REC-06 | 6 |
| FR-09 | 余额流水查询 | BAL-01 ~ BAL-03、E2E-01 | 4 |
| FR-10 | 操作审计与追溯 | AUD-01 ~ AUD-04、E2E-01 | 5 |
| FR-11 | 端到端业务闭环 | E2E-01 | 1 |

## 7. 执行说明

```bash
# 前置：后端（8002）与前端（5174）均已启动
/Users/wadesong/Desktop/TEST/DRVACLAW/Backend/.venv/bin/python3 \
  /Users/wadesong/Desktop/TEST/DRVACLAW/TEST/UAT/uat_test_suite.py
```

脚本执行后将产生：

| 产物 | 路径 | 说明 |
| --- | --- | --- |
| 验收测试报告 | `report/UAT_TEST_REPORT.html` | 汇总统计、模块通过率、缺陷清单、逐条结果 |
| 原始结果 | `report/results.json` | 机器可读的逐条执行结果 |
| JUnit 报告 | `report/junit.xml` | 可接入 CI 的标准化结果 |

## 8. 结果判定标准

| 结论 | 判定条件 |
| --- | --- |
| 通过（PASS） | 实际结果完全满足该用例预期结果 |
| 失败（FAIL） | 实际结果与预期不符（含状态码、字段值、数据一致性、审计记录） |
| 验收通过建议 | P0 用例 100% 通过，且 P1/P2 失败项均已评估为不影响主流程 |
