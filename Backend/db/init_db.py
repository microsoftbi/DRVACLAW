import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../drvaclaw.db')

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS area (
            area_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS person (
            person_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            register_time TEXT NOT NULL,
            area_id INTEGER,
            type TEXT NOT NULL CHECK(type IN ('学员', '教练')),
            FOREIGN KEY (area_id) REFERENCES area(area_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointment (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            coach_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            start_time INTEGER NOT NULL CHECK(start_time BETWEEN 1 AND 24),
            end_time INTEGER NOT NULL CHECK(end_time BETWEEN 1 AND 24),
            status TEXT NOT NULL CHECK(status IN ('待确认', '已确认', '已取消', '已完成')),
            create_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES person(person_id),
            FOREIGN KEY (coach_id) REFERENCES person(person_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recharge (
            recharge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            course_count INTEGER NOT NULL CHECK(course_count > 0),
            recharge_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES person(person_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balance_record (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            area_id INTEGER,
            record_date TEXT NOT NULL,
            hours REAL NOT NULL,
            balance REAL NOT NULL DEFAULT 0,
            type TEXT NOT NULL CHECK(type IN ('充值', '课时消耗')),
            recharge_id INTEGER,
            appointment_id INTEGER,
            FOREIGN KEY (student_id) REFERENCES person(person_id),
            FOREIGN KEY (area_id) REFERENCES area(area_id),
            FOREIGN KEY (recharge_id) REFERENCES recharge(recharge_id),
            FOREIGN KEY (appointment_id) REFERENCES appointment(appointment_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_test_data():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 插入区域数据（郑州市各区）
    areas = [
        ('中原区',),
        ('二七区',),
        ('管城回族区',),
        ('金水区',),
        ('上街区',),
        ('惠济区',),
        ('中牟县',),
        ('巩义市',),
        ('荥阳市',),
        ('新密市',),
        ('新郑市',),
        ('登封市',)
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO area (name) VALUES (?)', areas)
    
    # 插入人员数据
    persons = []
    
    # 添加10个学员
    for i in range(1, 11):
        name = f'学员{i}'
        phone = f'13800138{str(i).zfill(3)}'
        register_time = f'2026-01-{str(i).zfill(2)}'
        area_id = (i % 12) + 1  # 分配到不同的区域
        persons.append((name, phone, register_time, area_id, '学员'))
    
    # 添加5个教练
    for i in range(1, 6):
        name = f'教练{i}'
        phone = f'13900139{str(i).zfill(3)}'
        register_time = f'2026-01-{str(i).zfill(2)}'
        area_id = (i % 12) + 1  # 分配到不同的区域
        persons.append((name, phone, register_time, area_id, '教练'))
    
    cursor.executemany('INSERT OR IGNORE INTO person (name, phone, register_time, area_id, type) VALUES (?, ?, ?, ?, ?)', persons)
    
    # 插入预约数据
    appointments = []
    statuses = ['待确认', '已确认', '已完成', '已取消']
    
    # 生成30条预约数据，日期分布在2026年1月到5月
    for i in range(1, 31):
        # 随机选择学员（1-10）
        student_id = (i % 10) + 1
        # 随机选择教练（11-15）
        coach_id = (i % 5) + 11
        # 随机生成日期：2026年1月到5月
        month = (i % 5) + 1  # 1-5月
        day = (i % 28) + 1   # 1-28日
        appointment_date = f'2026-{str(month).zfill(2)}-{str(day).zfill(2)}'
        # 随机生成时间：9-18点
        start_time = (i % 10) + 9  # 9-18点
        end_time = start_time + 2  # 持续2小时
        # 随机选择状态
        status = statuses[i % 4]
        # 生成创建时间（与预约日期相同）
        create_time = appointment_date
        
        appointments.append((student_id, coach_id, appointment_date, start_time, end_time, status, create_time))
    
    cursor.executemany('INSERT OR IGNORE INTO appointment (student_id, coach_id, appointment_date, start_time, end_time, status, create_time) VALUES (?, ?, ?, ?, ?, ?, ?)', appointments)
    
    # 暂时不生成充值表和余额表的测试数据
    # # 插入充值数据
    # recharges = []
    # 
    # # 为每个学员生成2-3条充值记录
    # for student_id in range(1, 11):
    #     # 生成2-3条充值记录
    #     for i in range(1, 4):
    #         # 随机生成充值金额（1000-5000）
    #         amount = 1000 + (i * 1000)
    #         # 随机生成课程数量（5-20）
    #         course_count = 5 + (i * 3)
    #         # 生成充值时间（2026年1月到3月）
    #         month = i
    #         day = (student_id % 28) + 1
    #         recharge_time = f'2026-{str(month).zfill(2)}-{str(day).zfill(2)}'
    #         
    #         recharges.append((student_id, amount, course_count, recharge_time))
    # 
    # cursor.executemany('INSERT OR IGNORE INTO recharge (student_id, amount, course_count, recharge_time) VALUES (?, ?, ?, ?)', recharges)
    # 
    # # 将充值记录同步到余额记录表
    # cursor.execute('''
    #     INSERT INTO balance_record (student_id, area_id, record_date, hours, type, recharge_id, appointment_id)
    #     SELECT r.student_id, p.area_id, SUBSTR(r.recharge_time, 1, 10), r.course_count, '充值', r.recharge_id, NULL
    #     FROM recharge r
    #     JOIN person p ON r.student_id = p.person_id
    # ''')
    # 
    # # 将已完成的预约记录同步到余额记录表
    # cursor.execute('''
    #     INSERT INTO balance_record (student_id, area_id, record_date, hours, type, recharge_id, appointment_id)
    #     SELECT a.student_id, p.area_id, a.appointment_date, (a.end_time - a.start_time), '课时消耗', NULL, a.appointment_id
    #     FROM appointment a
    #     JOIN person p ON a.student_id = p.person_id
    #     WHERE a.status = '已完成'
    # ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    insert_test_data()
    print('数据库初始化完成，测试数据已插入')
