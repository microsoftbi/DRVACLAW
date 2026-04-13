-- 区域表：存储区域信息
CREATE TABLE IF NOT EXISTS area (
    area_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 区域ID
    name TEXT NOT NULL UNIQUE -- 区域名称
);

-- 人员表：存储学员和教练信息
CREATE TABLE IF NOT EXISTS person (
    person_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 人员ID
    name TEXT NOT NULL, -- 姓名
    phone TEXT NOT NULL UNIQUE, -- 手机号
    register_time TEXT NOT NULL, -- 注册时间
    area_id INTEGER, -- 所属区域ID
    type TEXT NOT NULL CHECK(type IN ('学员', '教练')), -- 类型：学员或教练
    FOREIGN KEY (area_id) REFERENCES area(area_id)
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
    FOREIGN KEY (student_id) REFERENCES person(person_id),
    FOREIGN KEY (coach_id) REFERENCES person(person_id)
);

-- 充值表：存储学员充值记录
CREATE TABLE IF NOT EXISTS recharge (
    recharge_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 充值ID
    student_id INTEGER NOT NULL, -- 学员ID
    amount REAL NOT NULL CHECK(amount > 0), -- 充值金额
    course_count INTEGER NOT NULL CHECK(course_count > 0), -- 课程数量
    recharge_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 充值时间
    FOREIGN KEY (student_id) REFERENCES person(person_id)
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
    FOREIGN KEY (student_id) REFERENCES person(person_id),
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
    FOREIGN KEY (student_id) REFERENCES person(person_id),
    FOREIGN KEY (coach_id) REFERENCES person(person_id)
);
