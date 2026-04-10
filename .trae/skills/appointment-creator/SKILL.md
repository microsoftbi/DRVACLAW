---
name: "appointment-creator"
description: "提供学员信息和教练信息以及具体时间，来创建预约课程。当用户说'老赵，帮我创建一个课程'时触发。"
---

# 预约课程创建器

## 功能

该技能可以调用 `create_appointment` 方法来创建预约课程。
当用户说"老赵，帮我创建一个课程"时触发。

## 调用方式

当用户说"老赵，帮我创建一个课程"时，系统会从用户的提示词里依次确认以下信息：
1. 学员名
2. 学员区域
3. 教练名
4. 教练区域
5. 日期（格式：YYYY-MM-DD）
6. 开始时间（格式：1-24）
7. 结束时间（格式：1-24）
如果用户的提示词里无法提取到这些信息，那么就逐次的用户确认这些信息。
如果用户提及的时间为比如今天，明天或者后天，那么就根据当前日期来计算预约日期。
如果用户提及的时间比如下午2点到4点，那么就自动转换成24小时格式的，比如下午2点到4点，就转换成14点到16点。
当所有信息都确认后，把这些信息汇总给用户让用户确认之后再调用 `create_appointment` 方法来创建预约课程。

## 实现细节

该技能会调用 `SKILLS/SKILL.py` 中的 `create_appointment` 方法，传入用户提供的参数。方法会：

1. 根据学员名和学员区域获取学员ID
2. 根据教练名和教练区域获取教练ID
3. 根据区域名获取区域ID
4. 调用FastAPI的API创建预约课程

## 代码实现

```python
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

```

## 依赖项

- `requests`：用于发送HTTP请求

## 安装依赖

```bash
pip install requests
```


## 示例

**用户：** 老赵，帮我创建一个课程

**系统：** 请提供以下信息：
1. 学员名：
2. 学员区域：
3. 教练名：
4. 教练区域：
5. 日期（格式：YYYY-MM-DD）：
6. 开始时间（格式：1-24）：
7. 结束时间（格式：1-24）：

**用户：** 学员名：张三，学员区域：中原区，教练名：李四，教练区域：中原区，日期：2026-04-10，开始时间：9，结束时间：11

**系统：** 预约课程创建成功，预约ID：1

**用户：** 老赵，帮我创建一个课程，金水区的学员3，金水区的教练3，在明天，下午2点到4点
**系统：** 好的，请提确认下信息：
1. 学员名：学员3
2. 学员区域：金水区
3. 教练名：教练3
4. 教练区域：金水区
5. 日期（格式：YYYY-MM-DD）：2026-04-12
6. 开始时间（格式：1-24）：14
7. 结束时间（格式：1-24）：16
**用户：** 确认
**系统：** 预约课程创建成功，预约ID：2