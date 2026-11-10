# 驾驶陪练小龙虾 API 文档

## 项目概述

驾驶陪练小龙虾 API 是一个基于 FastAPI 构建的后端服务，提供了驾驶陪练系统的核心功能，包括区域管理、学员管理、教练管理、车辆管理、预约管理、充值管理、余额记录和操作审计等功能。

接口BASE_URL: http://localhost:8002/

## 接口列表

### 1. 区域管理

| 接口路径 | 方法 | 功能描述 |
|---------|------|----------|
| `/api/areas` | POST | 创建区域 |
| `/api/areas` | GET | 获取所有区域 |
| `/api/areas/{area_id}` | GET | 获取指定区域 |
| `/api/areas/{area_id}` | PUT | 更新区域 |
| `/api/areas/{area_id}` | DELETE | 删除区域 |

### 2. 学员管理 / 教练管理 / 车辆管理

学员（`/api/students`）与教练（`/api/coaches`）分别使用独立的表与ID，教练通过 `vehicle_ids` 关联多辆车。

| 接口路径 | 方法 | 功能描述 |
|---------|------|----------|
| `/api/students` | POST | 创建学员 |
| `/api/students` | GET | 获取所有学员 |
| `/api/students/{student_id}` | GET | 获取指定学员 |
| `/api/students/{student_id}` | PUT | 更新学员 |
| `/api/students/{student_id}` | DELETE | 删除学员 |
| `/api/coaches` | POST | 创建教练（可同时关联车辆） |
| `/api/coaches` | GET | 获取所有教练（含关联车辆ID） |
| `/api/coaches/{coach_id}` | GET | 获取指定教练 |
| `/api/coaches/{coach_id}/vehicles` | GET | 获取教练关联的车辆列表 |
| `/api/coaches/{coach_id}` | PUT | 更新教练（可重新设置关联车辆） |
| `/api/coaches/{coach_id}` | DELETE | 删除教练 |
| `/api/vehicles` | POST | 创建车辆 |
| `/api/vehicles` | GET | 获取所有车辆 |
| `/api/vehicles/{vehicle_id}` | GET | 获取指定车辆 |
| `/api/vehicles/{vehicle_id}` | PUT | 更新车辆 |
| `/api/vehicles/{vehicle_id}` | DELETE | 删除车辆 |

### 3. 预约管理

| 接口路径 | 方法 | 功能描述 |
|---------|------|----------|
| `/api/appointments` | POST | 创建预约 |
| `/api/appointments` | GET | 获取所有预约 |
| `/api/appointments/{appointment_id}` | GET | 获取指定预约 |
| `/api/appointments/student/{student_id}` | GET | 获取学员的预约 |
| `/api/appointments/coach/{coach_id}` | GET | 获取教练的预约 |
| `/api/appointments/date/{appointment_date}` | GET | 获取指定日期的预约 |
| `/api/appointments/{appointment_id}` | PUT | 更新预约 |
| `/api/appointments/{appointment_id}` | DELETE | 删除预约 |

### 4. 充值管理

| 接口路径 | 方法 | 功能描述 |
|---------|------|----------|
| `/api/recharges` | POST | 创建充值记录 |
| `/api/recharges` | GET | 获取所有充值记录 |
| `/api/recharges/student/{student_id}` | GET | 获取学员的充值记录 |
| `/api/recharges/{recharge_id}` | GET | 获取指定充值记录 |
| `/api/recharges/{recharge_id}` | PUT | 更新充值记录 |
| `/api/recharges/{recharge_id}` | DELETE | 删除充值记录 |

### 5. 余额记录

| 接口路径 | 方法 | 功能描述 |
|---------|------|----------|
| `/api/balance-records` | GET | 获取所有余额记录 |
| `/api/balance-records/student/{student_id}` | GET | 获取学员的余额记录 |
| `/api/balance-records/{record_id}` | GET | 获取指定余额记录 |

### 6. 操作审计

| 接口路径 | 方法 | 功能描述 |
|---------|------|----------|
| `/api/audit-logs/` | GET | 获取所有操作记录 |
| `/api/audit-logs/student/{student_id}` | GET | 获取学员相关的操作记录 |
| `/api/audit-logs/coach/{coach_id}` | GET | 获取教练相关的操作记录 |

### 7. 系统接口

| 接口路径 | 方法 | 功能描述 |
|---------|------|----------|
| `/` | GET | 系统欢迎信息 |
| `/health` | GET | 健康检查 |

## 接口详细信息

### 1. 区域管理

#### 创建区域
- **路径**: `/api/areas`
- **方法**: POST
- **功能**: 创建新的区域
- **输入参数**:
  - `name`: str (区域名称)
- **输出参数**:
  - `area_id`: int (区域ID)
  - `name`: str (区域名称)
- **示例**:
  ```json
  // 输入
  {
    "name": "中原区"
  }
  
  // 输出
  {
    "area_id": 1,
    "name": "中原区"
  }
  ```

#### 获取所有区域
- **路径**: `/api/areas`
- **方法**: GET
- **功能**: 获取所有区域列表
- **输入参数**: 无
- **输出参数**: 区域列表，每个区域包含:
  - `area_id`: int (区域ID)
  - `name`: str (区域名称)

#### 获取指定区域
- **路径**: `/api/areas/{area_id}`
- **方法**: GET
- **功能**: 获取指定ID的区域信息
- **输入参数**:
  - `area_id`: int (区域ID)
- **输出参数**:
  - `area_id`: int (区域ID)
  - `name`: str (区域名称)

#### 更新区域
- **路径**: `/api/areas/{area_id}`
- **方法**: PUT
- **功能**: 更新指定ID的区域信息
- **输入参数**:
  - `area_id`: int (区域ID)
  - `name`: str (区域名称)
- **输出参数**:
  - `area_id`: int (区域ID)
  - `name`: str (区域名称)

#### 删除区域
- **路径**: `/api/areas/{area_id}`
- **方法**: DELETE
- **功能**: 删除指定ID的区域
- **输入参数**:
  - `area_id`: int (区域ID)
- **输出参数**:
  - `message`: str (删除成功消息)

### 2. 学员管理 / 教练管理 / 车辆管理

#### 创建学员
- **路径**: `/api/students`
- **方法**: POST
- **功能**: 创建新的学员
- **输入参数**:
  - `name`: str (姓名)
  - `phone`: str (手机号)
  - `area_id`: int (可选，所属区域ID)
  - `driving_years`: int (可选，驾龄，单位年，默认0)
  - `remark`: str (可选，备注)
- **输出参数**:
  - `student_id`: int (学员ID)
  - `name`: str (姓名)
  - `phone`: str (手机号)
  - `register_time`: str (注册时间)
  - `area_id`: int (所属区域ID)
  - `driving_years`: int (驾龄)
  - `remark`: str (备注)
- **示例**:
  ```json
  // 输入
  {
    "name": "张三",
    "phone": "13800138000",
    "area_id": 1,
    "driving_years": 3,
    "remark": "周末可练车"
  }

  // 输出
  {
    "student_id": 1,
    "name": "张三",
    "phone": "13800138000",
    "register_time": "2026-04-13 10:00:00",
    "area_id": 1,
    "driving_years": 3,
    "remark": "周末可练车"
  }
  ```

#### 获取所有学员
- **路径**: `/api/students`
- **方法**: GET
- **功能**: 获取所有学员列表
- **输出参数**: 学员列表，字段同上

#### 获取指定学员
- **路径**: `/api/students/{student_id}`
- **方法**: GET
- **功能**: 获取指定ID的学员信息

#### 更新学员
- **路径**: `/api/students/{student_id}`
- **方法**: PUT
- **功能**: 更新指定ID的学员信息
- **输入参数**:
  - `name`: str (可选，姓名)
  - `phone`: str (可选，手机号)
  - `area_id`: int (可选，所属区域ID)
  - `driving_years`: int (可选，驾龄)
  - `remark`: str (可选，备注)

#### 删除学员
- **路径**: `/api/students/{student_id}`
- **方法**: DELETE
- **功能**: 删除指定ID的学员
- **输出参数**:
  - `message`: str (删除成功消息)

#### 创建教练
- **路径**: `/api/coaches`
- **方法**: POST
- **功能**: 创建新的教练，可同时关联多辆车
- **输入参数**:
  - `name`: str (姓名)
  - `phone`: str (手机号)
  - `area_id`: int (可选，所属区域ID)
  - `vehicle_ids`: int[] (可选，关联的车辆ID列表)
- **输出参数**:
  - `coach_id`: int (教练ID)
  - `name`: str (姓名)
  - `phone`: str (手机号)
  - `register_time`: str (注册时间)
  - `area_id`: int (所属区域ID)
  - `vehicle_ids`: int[] (关联的车辆ID列表)
- **示例**:
  ```json
  // 输入
  {
    "name": "李教练",
    "phone": "13900139000",
    "area_id": 1,
    "vehicle_ids": [1, 2]
  }

  // 输出
  {
    "coach_id": 1,
    "name": "李教练",
    "phone": "13900139000",
    "register_time": "2026-04-13 10:00:00",
    "area_id": 1,
    "vehicle_ids": [1, 2]
  }
  ```

#### 获取所有教练
- **路径**: `/api/coaches`
- **方法**: GET
- **功能**: 获取所有教练列表，每个教练含 `vehicle_ids`

#### 获取指定教练
- **路径**: `/api/coaches/{coach_id}`
- **方法**: GET
- **功能**: 获取指定ID的教练信息

#### 获取教练关联车辆
- **路径**: `/api/coaches/{coach_id}/vehicles`
- **方法**: GET
- **功能**: 获取该教练关联的车辆列表（含 `vehicle_id`、`vehicle_type`、`brand`、`model`）

#### 更新教练
- **路径**: `/api/coaches/{coach_id}`
- **方法**: PUT
- **功能**: 更新指定ID的教练信息
- **输入参数**:
  - `name`: str (可选，姓名)
  - `phone`: str (可选，手机号)
  - `area_id`: int (可选，所属区域ID)
  - `vehicle_ids`: int[] (可选，重新设置关联车辆；不传则保持原关联)

#### 删除教练
- **路径**: `/api/coaches/{coach_id}`
- **方法**: DELETE
- **功能**: 删除指定ID的教练，同时解除其车辆关联
- **输出参数**:
  - `message`: str (删除成功消息)

#### 创建车辆
- **路径**: `/api/vehicles`
- **方法**: POST
- **功能**: 创建新的车辆
- **输入参数**:
  - `vehicle_type`: str (车型，值为"SUV"或"轿车")
  - `brand`: str (品牌)
  - `model`: str (型号)
- **输出参数**:
  - `vehicle_id`: int (车辆ID)
  - `vehicle_type`: str (车型)
  - `brand`: str (品牌)
  - `model`: str (型号)
  - `create_time`: str (创建时间)

#### 获取所有车辆
- **路径**: `/api/vehicles`
- **方法**: GET
- **功能**: 获取所有车辆列表

#### 获取指定车辆
- **路径**: `/api/vehicles/{vehicle_id}`
- **方法**: GET
- **功能**: 获取指定ID的车辆信息

#### 更新车辆
- **路径**: `/api/vehicles/{vehicle_id}`
- **方法**: PUT
- **功能**: 更新指定ID的车辆信息
- **输入参数**:
  - `vehicle_type`: str (可选，车型)
  - `brand`: str (可选，品牌)
  - `model`: str (可选，型号)

#### 删除车辆
- **路径**: `/api/vehicles/{vehicle_id}`
- **方法**: DELETE
- **功能**: 删除指定ID的车辆，同时解除教练对该车的关联
- **输出参数**:
  - `message`: str (删除成功消息)

### 3. 预约管理

#### 创建预约
- **路径**: `/api/appointments`
- **方法**: POST
- **功能**: 创建新的课程预约
- **输入参数**:
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `appointment_date`: str (预约日期，格式为YYYY-MM-DD)
  - `start_time`: int (开始时间，1-24)
  - `end_time`: int (结束时间，1-24)
  - `status`: str (状态，值为"待确认"、"已确认"、"已取消"或"已完成")
- **输出参数**:
  - `appointment_id`: int (预约ID)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `appointment_date`: str (预约日期)
  - `start_time`: int (开始时间)
  - `end_time`: int (结束时间)
  - `status`: str (状态)
  - `create_time`: str (创建时间)
- **示例**:
  ```json
  // 输入
  {
    "student_id": 1,
    "coach_id": 2,
    "appointment_date": "2026-04-14",
    "start_time": 14,
    "end_time": 16,
    "status": "待确认"
  }
  
  // 输出
  {
    "appointment_id": 1,
    "student_id": 1,
    "coach_id": 2,
    "appointment_date": "2026-04-14",
    "start_time": 14,
    "end_time": 16,
    "status": "待确认",
    "create_time": "2026-04-13 10:00:00"
  }
  ```

#### 获取所有预约
- **路径**: `/api/appointments`
- **方法**: GET
- **功能**: 获取所有预约列表
- **输入参数**: 无
- **输出参数**: 预约列表，每个预约包含:
  - `appointment_id`: int (预约ID)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `appointment_date`: str (预约日期)
  - `start_time`: int (开始时间)
  - `end_time`: int (结束时间)
  - `status`: str (状态)
  - `create_time`: str (创建时间)

#### 获取指定预约
- **路径**: `/api/appointments/{appointment_id}`
- **方法**: GET
- **功能**: 获取指定ID的预约信息
- **输入参数**:
  - `appointment_id`: int (预约ID)
- **输出参数**:
  - `appointment_id`: int (预约ID)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `appointment_date`: str (预约日期)
  - `start_time`: int (开始时间)
  - `end_time`: int (结束时间)
  - `status`: str (状态)
  - `create_time`: str (创建时间)

#### 获取学员的预约
- **路径**: `/api/appointments/student/{student_id}`
- **方法**: GET
- **功能**: 获取指定学员的所有预约
- **输入参数**:
  - `student_id`: int (学员ID)
- **输出参数**: 预约列表，每个预约包含:
  - `appointment_id`: int (预约ID)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `appointment_date`: str (预约日期)
  - `start_time`: int (开始时间)
  - `end_time`: int (结束时间)
  - `status`: str (状态)
  - `create_time`: str (创建时间)

#### 获取教练的预约
- **路径**: `/api/appointments/coach/{coach_id}`
- **方法**: GET
- **功能**: 获取指定教练的所有预约
- **输入参数**:
  - `coach_id`: int (教练ID)
- **输出参数**: 预约列表，每个预约包含:
  - `appointment_id`: int (预约ID)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `appointment_date`: str (预约日期)
  - `start_time`: int (开始时间)
  - `end_time`: int (结束时间)
  - `status`: str (状态)
  - `create_time`: str (创建时间)

#### 获取指定日期的预约
- **路径**: `/api/appointments/date/{appointment_date}`
- **方法**: GET
- **功能**: 获取指定日期的所有预约
- **输入参数**:
  - `appointment_date`: str (预约日期，格式为YYYY-MM-DD)
- **输出参数**: 预约列表，每个预约包含:
  - `appointment_id`: int (预约ID)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `appointment_date`: str (预约日期)
  - `start_time`: int (开始时间)
  - `end_time`: int (结束时间)
  - `status`: str (状态)
  - `create_time`: str (创建时间)

#### 更新预约
- **路径**: `/api/appointments/{appointment_id}`
- **方法**: PUT
- **功能**: 更新指定ID的预约信息
- **输入参数**:
  - `appointment_id`: int (预约ID)
  - `student_id`: int (可选，学员ID)
  - `coach_id`: int (可选，教练ID)
  - `appointment_date`: str (可选，预约日期)
  - `start_time`: int (可选，开始时间)
  - `end_time`: int (可选，结束时间)
  - `status`: str (可选，状态)
- **输出参数**:
  - `appointment_id`: int (预约ID)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `appointment_date`: str (预约日期)
  - `start_time`: int (开始时间)
  - `end_time`: int (结束时间)
  - `status`: str (状态)
  - `create_time`: str (创建时间)

#### 删除预约
- **路径**: `/api/appointments/{appointment_id}`
- **方法**: DELETE
- **功能**: 删除指定ID的预约
- **输入参数**:
  - `appointment_id`: int (预约ID)
- **输出参数**:
  - `message`: str (删除成功消息)

### 4. 充值管理

#### 创建充值记录
- **路径**: `/api/recharges`
- **方法**: POST
- **功能**: 创建新的充值记录
- **输入参数**:
  - `student_id`: int (学员ID)
  - `amount`: float (充值金额，大于0)
  - `course_count`: int (课程数量，大于0)
  - `recharge_time`: str (充值时间)
- **输出参数**:
  - `recharge_id`: int (充值ID)
  - `student_id`: int (学员ID)
  - `amount`: float (充值金额)
  - `course_count`: int (课程数量)
  - `recharge_time`: str (充值时间)
- **示例**:
  ```json
  // 输入
  {
    "student_id": 1,
    "amount": 1000,
    "course_count": 10,
    "recharge_time": "2026-04-13 10:00:00"
  }
  
  // 输出
  {
    "recharge_id": 1,
    "student_id": 1,
    "amount": 1000,
    "course_count": 10,
    "recharge_time": "2026-04-13 10:00:00"
  }
  ```

#### 获取所有充值记录
- **路径**: `/api/recharges`
- **方法**: GET
- **功能**: 获取所有充值记录列表
- **输入参数**: 无
- **输出参数**: 充值记录列表，每个充值记录包含:
  - `recharge_id`: int (充值ID)
  - `student_id`: int (学员ID)
  - `amount`: float (充值金额)
  - `course_count`: int (课程数量)
  - `recharge_time`: str (充值时间)

#### 获取学员的充值记录
- **路径**: `/api/recharges/student/{student_id}`
- **方法**: GET
- **功能**: 获取指定学员的所有充值记录
- **输入参数**:
  - `student_id`: int (学员ID)
- **输出参数**: 充值记录列表，每个充值记录包含:
  - `recharge_id`: int (充值ID)
  - `student_id`: int (学员ID)
  - `amount`: float (充值金额)
  - `course_count`: int (课程数量)
  - `recharge_time`: str (充值时间)

#### 获取指定充值记录
- **路径**: `/api/recharges/{recharge_id}`
- **方法**: GET
- **功能**: 获取指定ID的充值记录
- **输入参数**:
  - `recharge_id`: int (充值ID)
- **输出参数**:
  - `recharge_id`: int (充值ID)
  - `student_id`: int (学员ID)
  - `amount`: float (充值金额)
  - `course_count`: int (课程数量)
  - `recharge_time`: str (充值时间)

#### 更新充值记录
- **路径**: `/api/recharges/{recharge_id}`
- **方法**: PUT
- **功能**: 更新指定ID的充值记录
- **输入参数**:
  - `recharge_id`: int (充值ID)
  - `student_id`: int (学员ID)
  - `amount`: float (充值金额，大于0)
  - `course_count`: int (课程数量，大于0)
  - `recharge_time`: str (充值时间)
- **输出参数**:
  - `recharge_id`: int (充值ID)
  - `student_id`: int (学员ID)
  - `amount`: float (充值金额)
  - `course_count`: int (课程数量)
  - `recharge_time`: str (充值时间)

#### 删除充值记录
- **路径**: `/api/recharges/{recharge_id}`
- **方法**: DELETE
- **功能**: 删除指定ID的充值记录
- **输入参数**:
  - `recharge_id`: int (充值ID)
- **输出参数**:
  - `message`: str (删除成功消息)

### 5. 余额记录

#### 获取所有余额记录
- **路径**: `/api/balance-records`
- **方法**: GET
- **功能**: 获取所有余额记录列表
- **输入参数**: 无
- **输出参数**: 余额记录列表，每个余额记录包含:
  - `record_id`: int (记录ID)
  - `student_id`: int (学员ID)
  - `area_id`: int (所属区域ID)
  - `record_date`: str (记录日期)
  - `hours`: float (课时数)
  - `balance`: float (结余)
  - `type`: str (类型，值为"充值"或"课时消耗")
  - `recharge_id`: int (关联的充值ID)
  - `appointment_id`: int (关联的预约ID)

#### 获取学员的余额记录
- **路径**: `/api/balance-records/student/{student_id}`
- **方法**: GET
- **功能**: 获取指定学员的所有余额记录
- **输入参数**:
  - `student_id`: int (学员ID)
- **输出参数**: 余额记录列表，每个余额记录包含:
  - `record_id`: int (记录ID)
  - `student_id`: int (学员ID)
  - `area_id`: int (所属区域ID)
  - `record_date`: str (记录日期)
  - `hours`: float (课时数)
  - `balance`: float (结余)
  - `type`: str (类型)
  - `recharge_id`: int (关联的充值ID)
  - `appointment_id`: int (关联的预约ID)

#### 获取指定余额记录
- **路径**: `/api/balance-records/{record_id}`
- **方法**: GET
- **功能**: 获取指定ID的余额记录
- **输入参数**:
  - `record_id`: int (记录ID)
- **输出参数**:
  - `record_id`: int (记录ID)
  - `student_id`: int (学员ID)
  - `area_id`: int (所属区域ID)
  - `record_date`: str (记录日期)
  - `hours`: float (课时数)
  - `balance`: float (结余)
  - `type`: str (类型)
  - `recharge_id`: int (关联的充值ID)
  - `appointment_id`: int (关联的预约ID)

### 6. 操作审计

#### 获取所有操作记录
- **路径**: `/api/audit-logs/`
- **方法**: GET
- **功能**: 获取所有操作记录列表
- **输入参数**: 无
- **输出参数**: 操作记录列表，每个操作记录包含:
  - `audit_id`: int (审计ID)
  - `operator`: str (操作人)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `operation_time`: str (操作时间)
  - `operation_type`: str (操作类型)
  - `operation_result`: str (操作结果)

#### 获取学员相关的操作记录
- **路径**: `/api/audit-logs/student/{student_id}`
- **方法**: GET
- **功能**: 获取指定学员相关的所有操作记录
- **输入参数**:
  - `student_id`: int (学员ID)
- **输出参数**: 操作记录列表，每个操作记录包含:
  - `audit_id`: int (审计ID)
  - `operator`: str (操作人)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `operation_time`: str (操作时间)
  - `operation_type`: str (操作类型)
  - `operation_result`: str (操作结果)

#### 获取教练相关的操作记录
- **路径**: `/api/audit-logs/coach/{coach_id}`
- **方法**: GET
- **功能**: 获取指定教练相关的所有操作记录
- **输入参数**:
  - `coach_id`: int (教练ID)
- **输出参数**: 操作记录列表，每个操作记录包含:
  - `audit_id`: int (审计ID)
  - `operator`: str (操作人)
  - `student_id`: int (学员ID)
  - `coach_id`: int (教练ID)
  - `operation_time`: str (操作时间)
  - `operation_type`: str (操作类型)
  - `operation_result`: str (操作结果)

### 7. 系统接口

#### 系统欢迎信息
- **路径**: `/`
- **方法**: GET
- **功能**: 获取系统欢迎信息
- **输入参数**: 无
- **输出参数**:
  - `message`: str (欢迎消息)

#### 健康检查
- **路径**: `/health`
- **方法**: GET
- **功能**: 检查系统健康状态
- **输入参数**: 无
- **输出参数**:
  - `status`: str (健康状态)

## 错误处理

所有接口在遇到错误时，会返回以下格式的错误信息：

```json
{
  "detail": "错误信息"
}
```

常见错误状态码：
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误

## 接口版本

当前API版本：1.0.0
