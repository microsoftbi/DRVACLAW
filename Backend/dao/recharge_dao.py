import sqlite3
from typing import List, Dict
from Backend.db.connection import get_connection
from Backend.dao.audit_log_dao import AuditLogDAO

class RechargeDAO:
    @staticmethod
    def create(student_id: int, amount: float, course_count: int, recharge_time: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 开始事务
        conn.execute('BEGIN TRANSACTION')
        try:
            # 插入充值记录
            cursor.execute(
                'INSERT INTO recharge (student_id, amount, course_count, recharge_time) VALUES (?, ?, ?, ?)',
                (student_id, amount, course_count, recharge_time)
            )
            recharge_id = cursor.lastrowid
            
            # 获取学员的区域ID
            cursor.execute('SELECT area_id FROM person WHERE person_id = ?', (student_id,))
            student = cursor.fetchone()
            area_id = student[0] if student else None
            
            # 计算当前结余
            cursor.execute('SELECT SUM(hours) FROM balance_record WHERE student_id = ?', (student_id,))
            current_balance = cursor.fetchone()[0] or 0
            new_balance = current_balance + course_count
            
            # 插入余额记录
            # 使用完整的日期时间
            record_date = recharge_time if recharge_time else ''
            cursor.execute(
                'INSERT INTO balance_record (student_id, area_id, record_date, hours, balance, type, recharge_id, appointment_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (student_id, area_id, record_date, course_count, new_balance, '充值', recharge_id, None)
            )
            
            # 提交事务
            conn.commit()
            
            # 添加操作审计记录
            AuditLogDAO.create(
                operator="系统",
                operation_type="充值",
                operation_result=f"充值成功，充值记录ID为{recharge_id}",
                student_id=student_id,
                coach_id=None  # 充值操作不需要教练ID
            )
            
            return recharge_id
        except Exception as e:
            # 回滚事务
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_by_id(recharge_id: int) -> Dict:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM recharge WHERE recharge_id = ?', (recharge_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM recharge ORDER BY recharge_id DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_student_id(student_id: int) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM recharge WHERE student_id = ? ORDER BY recharge_id DESC', (student_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def update(recharge_id: int, student_id: int, amount: float, course_count: int, recharge_time: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 开始事务
        conn.execute('BEGIN TRANSACTION')
        try:
            # 更新充值记录
            cursor.execute(
                'UPDATE recharge SET student_id = ?, amount = ?, course_count = ?, recharge_time = ? WHERE recharge_id = ?',
                (student_id, amount, course_count, recharge_time, recharge_id)
            )
            affected_rows = cursor.rowcount
            
            if affected_rows > 0:
                # 获取学员的区域ID
                cursor.execute('SELECT area_id FROM person WHERE person_id = ?', (student_id,))
                student = cursor.fetchone()
                area_id = student[0] if student else None
                
                # 使用完整的日期时间
                record_date = recharge_time if recharge_time else ''
                
                # 更新余额记录
                cursor.execute(
                    'UPDATE balance_record SET student_id = ?, area_id = ?, record_date = ?, hours = ? WHERE recharge_id = ?',
                    (student_id, area_id, record_date, course_count, recharge_id)
                )
                
                # 重新计算该学员所有余额记录的结余
                cursor.execute('SELECT record_id, hours FROM balance_record WHERE student_id = ? ORDER BY record_date ASC, record_id ASC', (student_id,))
                records = cursor.fetchall()
                
                current_balance = 0
                for record in records:
                    record_id = record[0]
                    hours = record[1]
                    current_balance += hours
                    cursor.execute('UPDATE balance_record SET balance = ? WHERE record_id = ?', (current_balance, record_id))
            
            # 提交事务
            conn.commit()
            
            # 添加操作审计记录
            if affected_rows > 0:
                AuditLogDAO.create(
                    operator="系统",
                    operation_type="修改充值",
                    operation_result=f"修改充值成功，充值记录ID为{recharge_id}",
                    student_id=student_id,
                    coach_id=None  # 充值操作不需要教练ID
                )
            
            return affected_rows > 0
        except Exception as e:
            # 回滚事务
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete(recharge_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 开始事务
        conn.execute('BEGIN TRANSACTION')
        try:
            # 获取被删除的充值记录对应的学生ID
            cursor.execute('SELECT student_id FROM balance_record WHERE recharge_id = ?', (recharge_id,))
            student_row = cursor.fetchone()
            student_id = student_row[0] if student_row else None
            
            # 删除余额记录
            cursor.execute('DELETE FROM balance_record WHERE recharge_id = ?', (recharge_id,))
            
            # 删除充值记录
            cursor.execute('DELETE FROM recharge WHERE recharge_id = ?', (recharge_id,))
            affected_rows = cursor.rowcount
            
            # 重新计算该学员所有余额记录的结余
            if student_id:
                cursor.execute('SELECT record_id, hours FROM balance_record WHERE student_id = ? ORDER BY record_date ASC, record_id ASC', (student_id,))
                records = cursor.fetchall()
                
                current_balance = 0
                for record in records:
                    record_id = record[0]
                    hours = record[1]
                    current_balance += hours
                    cursor.execute('UPDATE balance_record SET balance = ? WHERE record_id = ?', (current_balance, record_id))
            
            # 提交事务
            conn.commit()
            
            # 添加操作审计记录
            if affected_rows > 0 and student_id:
                AuditLogDAO.create(
                    operator="系统",
                    operation_type="删除充值",
                    operation_result=f"删除充值成功，充值记录ID为{recharge_id}",
                    student_id=student_id,
                    coach_id=None  # 充值操作不需要教练ID
                )
            
            return affected_rows > 0
        except Exception as e:
            # 回滚事务
            conn.rollback()
            raise e
        finally:
            conn.close()