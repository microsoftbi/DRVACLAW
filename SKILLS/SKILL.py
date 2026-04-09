import requests

# FastAPI服务器地址
BASE_URL = "http://localhost:8002"

def create_appointment(student_name, student_area, coach_name, coach_area, date, start_time, end_time):
    """
    创建预约课程
    
    Args:
        student_name: 学员名
        student_area: 学员区域
        coach_name: 教练名
        coach_area: 教练区域
        date: 日期，格式：YYYY-MM-DD
        start_time: 开始时间，格式：1-24
        end_time: 结束时间，格式：1-24
    
    Returns:
        dict: 创建结果
    """
    try:
        # 1. 获取区域ID
        areas = requests.get(f"{BASE_URL}/api/areas").json()
        student_area_id = None
        coach_area_id = None
        
        for area in areas:
            if area["name"] == student_area:
                student_area_id = area["area_id"]
            if area["name"] == coach_area:
                coach_area_id = area["area_id"]
        
        if not student_area_id:
            return {"error": f"未找到学员区域：{student_area}"}
        if not coach_area_id:
            return {"error": f"未找到教练区域：{coach_area}"}
        
        # 2. 获取学员ID
        students = requests.get(f"{BASE_URL}/api/persons/students").json()
        student_id = None
        
        for student in students:
            if student["name"] == student_name and student["area_id"] == student_area_id:
                student_id = student["person_id"]
                break
        
        if not student_id:
            raise Exception(f"未找到学员：{student_name} (区域：{student_area})")
        
        # 3. 获取教练ID
        coaches = requests.get(f"{BASE_URL}/api/persons/coaches").json()
        coach_id = None
        
        for coach in coaches:
            if coach["name"] == coach_name and coach["area_id"] == coach_area_id:
                coach_id = coach["person_id"]
                break
        
        if not coach_id:
            raise Exception(f"未找到教练：{coach_name} (区域：{coach_area})")
        
        # 4. 创建预约课程
        appointment_data = {
            "student_id": student_id,
            "coach_id": coach_id,
            "appointment_date": date,
            "start_time": start_time,
            "end_time": end_time,
            "status": "待确认"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=appointment_data)
        
        if response.status_code in [200, 201]:
            return {"success": True, "appointment_id": response.json()["appointment_id"]}
        else:
            return {"error": f"创建预约失败：{response.json()}"}
    
    except Exception as e:
        return {"error": f"发生错误：{str(e)}"}

# 示例调用
if __name__ == "__main__":
    result = create_appointment(
        student_name="测试学员",
        student_area="中原区",
        coach_name="测试教练",
        coach_area="中原区",
        date="2026-04-10",
        start_time=9,
        end_time=11
    )
    print(result)

    result = create_appointment(
        student_name="学员3",
        student_area="金水区",
        coach_name="教练3",
        coach_area="金水区",
        date="2026-04-12",
        start_time=14,
        end_time=16
    )
    print(result)
