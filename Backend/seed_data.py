import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Backend.db.init_db import init_db
from Backend.dao.area_dao import AreaDAO
from Backend.dao.person_dao import PersonDAO
from Backend.dao.appointment_dao import AppointmentDAO
from datetime import datetime

def seed_areas():
    """添加河南郑州的区域数据"""
    zhengzhou_areas = [
        "中原区",
        "二七区",
        "管城回族区",
        "金水区",
        "上街区",
        "惠济区",
        "中牟县",
        "巩义市",
        "荥阳市",
        "新密市",
        "新郑市",
        "登封市"
    ]
    
    print("正在添加郑州区域数据...")
    for area_name in zhengzhou_areas:
        try:
            area_id = AreaDAO.create(area_name)
            print(f"  ✓ 已添加: {area_name} (ID: {area_id})")
        except Exception as e:
            print(f"  ✗ 添加失败: {area_name} - {e}")

def seed_persons():
    """添加测试人员数据"""
    print("\n正在添加测试人员数据...")
    
    students = [
        {"name": "张明", "phone": "13800138001", "type": "学员", "area_id": 1},
        {"name": "李华", "phone": "13800138002", "type": "学员", "area_id": 2},
        {"name": "王芳", "phone": "13800138003", "type": "学员", "area_id": 3},
    ]
    
    coaches = [
        {"name": "赵教练", "phone": "13900139001", "type": "教练", "area_id": 1},
        {"name": "钱教练", "phone": "13900139002", "type": "教练", "area_id": 2},
        {"name": "孙教练", "phone": "13900139003", "type": "教练", "area_id": 3},
    ]
    
    register_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for student in students:
        try:
            person_id = PersonDAO.create(
                student["name"],
                student["phone"],
                register_time,
                student["area_id"],
                student["type"]
            )
            print(f"  ✓ 已添加学员: {student['name']} (ID: {person_id})")
        except Exception as e:
            print(f"  ✗ 添加失败: {student['name']} - {e}")
    
    for coach in coaches:
        try:
            person_id = PersonDAO.create(
                coach["name"],
                coach["phone"],
                register_time,
                coach["area_id"],
                coach["type"]
            )
            print(f"  ✓ 已添加教练: {coach['name']} (ID: {person_id})")
        except Exception as e:
            print(f"  ✗ 添加失败: {coach['name']} - {e}")

def seed_appointments():
    """添加测试预约数据"""
    print("\n正在添加测试预约数据...")
    
    appointments = [
        {"student_id": 1, "coach_id": 4, "date": "2026-04-10", "start": 9, "end": 11, "status": "待确认"},
        {"student_id": 2, "coach_id": 5, "date": "2026-04-10", "start": 14, "end": 16, "status": "已确认"},
        {"student_id": 3, "coach_id": 6, "date": "2026-04-11", "start": 10, "end": 12, "status": "待确认"},
    ]
    
    for appt in appointments:
        try:
            appt_id = AppointmentDAO.create(
                appt["student_id"],
                appt["coach_id"],
                appt["date"],
                appt["start"],
                appt["end"],
                appt["status"]
            )
            print(f"  ✓ 已添加预约 (ID: {appt_id})")
        except Exception as e:
            print(f"  ✗ 添加预约失败 - {e}")

def main():
    print("=" * 50)
    print("驾驶陪练小龙虾 - 测试数据初始化")
    print("=" * 50)
    
    # 初始化数据库
    print("\n正在初始化数据库...")
    init_db()
    print("✓ 数据库初始化完成")
    
    # 添加测试数据
    seed_areas()
    seed_persons()
    seed_appointments()
    
    print("\n" + "=" * 50)
    print("✓ 测试数据添加完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()
