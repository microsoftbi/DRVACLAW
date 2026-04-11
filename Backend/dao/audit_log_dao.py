from typing import List, Dict
from Backend.db.connection import get_connection

class AuditLogDAO:
    @staticmethod
    def create(operator: str, operation_type: str, operation_result: str, student_id: int = None, coach_id: int = None) -> int:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            import datetime
            operation_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 打印调试信息
            print(f"Creating audit log: operator={operator}, operation_type={operation_type}, operation_result={operation_result}, student_id={student_id}, coach_id={coach_id}, operation_time={operation_time}")
            
            cursor.execute(
                'INSERT INTO audit_log (operator, student_id, coach_id, operation_time, operation_type, operation_result) VALUES (?, ?, ?, ?, ?, ?)',
                (operator, student_id, coach_id, operation_time, operation_type, operation_result)
            )
            
            audit_id = cursor.lastrowid
            conn.commit()
            conn.close()
            print(f"Audit log created successfully with id: {audit_id}")
            return audit_id
        except Exception as e:
            print(f"Error creating audit log: {e}")
            raise e
    
    @staticmethod
    def get_all() -> List[Dict]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM audit_log ORDER BY audit_id DESC')
            rows = cursor.fetchall()
            print(f"Found {len(rows)} audit logs")
            # 获取列名
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                print(f"Columns: {columns}")
                # 将元组转换为字典
                result = [dict(zip(columns, row)) for row in rows]
                print(f"Result: {result}")
                conn.close()
                return result
            else:
                print("No columns found")
                conn.close()
                return []
        except Exception as e:
            print(f"Error getting all audit logs: {e}")
            return []
    
    @staticmethod
    def get_by_student_id(student_id: int) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audit_log WHERE student_id = ? ORDER BY audit_id DESC', (student_id,))
        rows = cursor.fetchall()
        # 获取列名
        columns = [col[0] for col in cursor.description]
        conn.close()
        # 将元组转换为字典
        return [dict(zip(columns, row)) for row in rows]
    
    @staticmethod
    def get_by_coach_id(coach_id: int) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audit_log WHERE coach_id = ? ORDER BY audit_id DESC', (coach_id,))
        rows = cursor.fetchall()
        # 获取列名
        columns = [col[0] for col in cursor.description]
        conn.close()
        # 将元组转换为字典
        return [dict(zip(columns, row)) for row in rows]
