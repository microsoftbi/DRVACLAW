-- 区域表：存储区域信息
CREATE TABLE IF NOT EXISTS area (
    area_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 区域ID
    name TEXT NOT NULL UNIQUE -- 区域名称
);

-- 学员表：存储学员信息
CREATE TABLE IF NOT EXISTS student (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 学员ID
    name TEXT NOT NULL, -- 姓名
    phone TEXT NOT NULL UNIQUE, -- 手机号
    register_time TEXT NOT NULL, -- 注册时间
    area_id INTEGER, -- 所属区域ID
    driving_years INTEGER NOT NULL DEFAULT 0, -- 驾龄（年）
    remark TEXT, -- 备注
    FOREIGN KEY (area_id) REFERENCES area(area_id)
);

-- 教练表：存储教练信息
CREATE TABLE IF NOT EXISTS coach (
    coach_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 教练ID
    name TEXT NOT NULL, -- 姓名
    phone TEXT NOT NULL UNIQUE, -- 手机号
    register_time TEXT NOT NULL, -- 注册时间
    area_id INTEGER, -- 所属区域ID
    FOREIGN KEY (area_id) REFERENCES area(area_id)
);

-- 车辆表：存储教练可使用的车辆
CREATE TABLE IF NOT EXISTS vehicle (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 车辆ID
    vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('SUV', '轿车')), -- 车型
    brand TEXT NOT NULL, -- 品牌
    model TEXT NOT NULL, -- 型号
    create_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP -- 创建时间
);

-- 教练车辆关联表：一个教练可关联多辆车
CREATE TABLE IF NOT EXISTS coach_vehicle (
    coach_id INTEGER NOT NULL, -- 教练ID
    vehicle_id INTEGER NOT NULL, -- 车辆ID
    PRIMARY KEY (coach_id, vehicle_id),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id) ON DELETE CASCADE
);

-- 预约表：存储课程预约信息
CREATE TABLE IF NOT EXISTS appointment (
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 预约ID
    student_id INTEGER NOT NULL, -- 学员ID
    coach_id INTEGER NOT NULL, -- 教练ID
    appointment_date TEXT NOT NULL, -- 预约日期
    start_time INTEGER NOT NULL CHECK(start_time BETWEEN 1 AND 24), -- 开始时间（1-24）
    end_time INTEGER NOT NULL CHECK(end_time BETWEEN 1 AND 24), -- 结束时间（1-24）
    status TEXT NOT NULL CHECK(status IN ('待确认', '已确认', '已取消', '已完成')), -- 状态
    create_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 充值表：存储学员充值记录
CREATE TABLE IF NOT EXISTS recharge (
    recharge_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 充值ID
    student_id INTEGER NOT NULL, -- 学员ID
    amount REAL NOT NULL CHECK(amount > 0), -- 充值金额
    course_count INTEGER NOT NULL CHECK(course_count > 0), -- 课程数量
    recharge_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 充值时间
    FOREIGN KEY (student_id) REFERENCES student(student_id)
);

-- 余额记录表：存储学员余额变动记录
CREATE TABLE IF NOT EXISTS balance_record (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 记录ID
    student_id INTEGER NOT NULL, -- 学员ID
    area_id INTEGER, -- 所属区域ID
    record_date TEXT NOT NULL, -- 记录日期
    hours REAL NOT NULL, -- 课时数
    balance REAL NOT NULL DEFAULT 0, -- 结余
    type TEXT NOT NULL CHECK(type IN ('充值', '课时消耗')), -- 类型：充值或课时消耗
    recharge_id INTEGER, -- 关联的充值ID
    appointment_id INTEGER, -- 关联的预约ID
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (area_id) REFERENCES area(area_id),
    FOREIGN KEY (recharge_id) REFERENCES recharge(recharge_id),
    FOREIGN KEY (appointment_id) REFERENCES appointment(appointment_id)
);

-- 操作审计表：存储系统操作记录
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 审计ID
    operator TEXT NOT NULL, -- 操作人
    student_id INTEGER, -- 学员ID
    coach_id INTEGER, -- 教练ID
    operation_time TEXT NOT NULL, -- 操作时间
    operation_type TEXT NOT NULL, -- 操作类型
    operation_result TEXT NOT NULL, -- 操作结果
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (coach_id) REFERENCES coach(coach_id)
);

-- 常用查询索引：列表筛选与关联查询避免全表扫描
CREATE INDEX IF NOT EXISTS idx_appointment_student ON appointment(student_id);
CREATE INDEX IF NOT EXISTS idx_appointment_coach ON appointment(coach_id);
CREATE INDEX IF NOT EXISTS idx_appointment_date ON appointment(appointment_date);
CREATE INDEX IF NOT EXISTS idx_recharge_student ON recharge(student_id);
CREATE INDEX IF NOT EXISTS idx_balance_student ON balance_record(student_id);
CREATE INDEX IF NOT EXISTS idx_balance_recharge ON balance_record(recharge_id);
CREATE INDEX IF NOT EXISTS idx_balance_appointment ON balance_record(appointment_id);
CREATE INDEX IF NOT EXISTS idx_coach_vehicle_vehicle ON coach_vehicle(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_audit_student ON audit_log(student_id);
CREATE INDEX IF NOT EXISTS idx_audit_coach ON audit_log(coach_id);
