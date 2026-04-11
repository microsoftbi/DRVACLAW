import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../drvaclaw.db')

def insert_test_data():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 清空相关表
    cursor.execute('DELETE FROM balance_record')
    cursor.execute('DELETE FROM appointment')
    cursor.execute('DELETE FROM recharge')
    cursor.execute('DELETE FROM person')
    cursor.execute('DELETE FROM area')
    
    # 重置自增ID
    cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("balance_record", "appointment", "recharge", "person", "area")')
    
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
    
    cursor.executemany('INSERT INTO area (name) VALUES (?)', areas)
    
    # 常见中文姓氏列表
    surnames = [
        '王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴',
        '徐', '孙', '马', '朱', '胡', '郭', '何', '高', '林', '罗',
        '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹'
    ]
    
    import random
    
    # 插入人员数据
    persons = []
    
    # 添加10个学员
    for i in range(1, 11):
        surname = random.choice(surnames)
        name = f'{surname}学员'
        phone = f'13800138{str(i).zfill(3)}'
        register_time = f'2026-01-{str(i).zfill(2)}'
        area_id = (i % 12) + 1  # 分配到不同的区域
        persons.append((name, phone, register_time, area_id, '学员'))
    
    # 添加5个教练
    for i in range(1, 6):
        surname = random.choice(surnames)
        name = f'{surname}教练'
        phone = f'13900139{str(i).zfill(3)}'
        register_time = f'2026-01-{str(i).zfill(2)}'
        area_id = (i % 12) + 1  # 分配到不同的区域
        persons.append((name, phone, register_time, area_id, '教练'))
    
    cursor.executemany('INSERT OR IGNORE INTO person (name, phone, register_time, area_id, type) VALUES (?, ?, ?, ?, ?)', persons)
    
    # 插入预约数据
    appointments = []
    statuses = ['待确认', '已确认', '已取消']  # 不包含已完成
    
    # 计算未来一周的日期
    import datetime
    today = datetime.date.today()
    
    # 生成30条预约数据，日期为未来一周
    for i in range(1, 31):
        # 随机选择学员（1-10）
        student_id = (i % 10) + 1
        # 随机选择教练（11-15）
        coach_id = (i % 5) + 11
        # 生成未来一周的日期
        days_from_now = i % 7  # 0-6天
        appointment_date = (today + datetime.timedelta(days=days_from_now)).strftime('%Y-%m-%d')
        # 随机生成时间：9-18点
        start_time = (i % 10) + 9  # 9-18点
        end_time = start_time + 2  # 持续2小时
        # 随机选择状态
        status = statuses[i % 3]  # 只从待确认、已确认、已取消中选择
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
    insert_test_data()
    print('测试数据已插入')
