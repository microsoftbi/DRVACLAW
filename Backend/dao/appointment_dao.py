from typing import List, Optional, Dict
from Backend.db.connection import get_connection

class AppointmentDAO:
    @staticmethod
    def create(student_id: int, coach_id: int, appointment_date: str, start_time: int, end_time: int, status: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO appointment (student_id, coach_id, appointment_date, start_time, end_time, status) VALUES (?, ?, ?, ?, ?, ?)',
            (student_id, coach_id, appointment_date, start_time, end_time, status)
        )
        conn.commit()
        appointment_id = cursor.lastrowid
        conn.close()
        return appointment_id
    
    @staticmethod
    def get_by_id(appointment_id: int) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM appointment WHERE appointment_id = ?', (appointment_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def get_all() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM appointment ORDER BY appointment_id DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_student_id(student_id: int) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM appointment WHERE student_id = ?', (student_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_coach_id(coach_id: int) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM appointment WHERE coach_id = ?', (coach_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_date(appointment_date: str) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM appointment WHERE appointment_date = ?', (appointment_date,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def update(appointment_id: int, student_id: Optional[int] = None, coach_id: Optional[int] = None, 
               appointment_date: Optional[str] = None, start_time: Optional[int] = None, 
               end_time: Optional[int] = None, status: Optional[str] = None) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 开始事务
        conn.execute('BEGIN TRANSACTION')
        try:
            # 获取原预约信息
            cursor.execute('SELECT student_id, appointment_date, start_time, end_time, status FROM appointment WHERE appointment_id = ?', (appointment_id,))
            old_appointment = cursor.fetchone()
            
            if not old_appointment:
                conn.close()
                return False
            
            old_status = old_appointment[4]
            
            # 构建更新语句
            updates = []
            params = []
            
            if student_id is not None:
                updates.append('student_id = ?')
                params.append(student_id)
            if coach_id is not None:
                updates.append('coach_id = ?')
                params.append(coach_id)
            if appointment_date is not None:
                updates.append('appointment_date = ?')
                params.append(appointment_date)
            if start_time is not None:
                updates.append('start_time = ?')
                params.append(start_time)
            if end_time is not None:
                updates.append('end_time = ?')
                params.append(end_time)
            if status is not None:
                updates.append('status = ?')
                params.append(status)
            
            if not updates:
                conn.close()
                return False
            
            params.append(appointment_id)
            cursor.execute(f'UPDATE appointment SET {", ".join(updates)} WHERE appointment_id = ?', params)
            
            # 检查是否更新成功
            updated = cursor.rowcount > 0
            
            # 如果状态从非已完成变为已完成，添加余额记录
            if updated and status == '已完成' and old_status != '已完成':
                # 获取更新后的预约信息
                cursor.execute('SELECT student_id, appointment_date, start_time, end_time, create_time FROM appointment WHERE appointment_id = ?', (appointment_id,))
                new_appointment = cursor.fetchone()
                
                if new_appointment:
                    student_id_val = new_appointment[0]
                    # 使用当前时间作为记录日期
                    import datetime
                    record_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    start_time_val = new_appointment[2]
                    end_time_val = new_appointment[3]
                    
                    # 计算课时（结束时间 - 开始时间），对于课时消耗记录，使用负数
                    hours = -(end_time_val - start_time_val)
                    
                    # 获取学员的区域ID
                    cursor.execute('SELECT area_id FROM person WHERE person_id = ?', (student_id_val,))
                    student = cursor.fetchone()
                    area_id = student[0] if student else None
                    
                    # 计算当前结余
                    cursor.execute('SELECT SUM(hours) FROM balance_record WHERE student_id = ?', (student_id_val,))
                    current_balance = cursor.fetchone()[0] or 0
                    new_balance = current_balance + hours
                    
                    # 插入余额记录
                    cursor.execute(
                        'INSERT INTO balance_record (student_id, area_id, record_date, hours, balance, type, recharge_id, appointment_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (student_id_val, area_id, record_date, hours, new_balance, '课时消耗', None, appointment_id)
                    )
            
            # 提交事务
            conn.commit()
            return updated
        except Exception as e:
            # 回滚事务
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def delete(appointment_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 开始事务
        conn.execute('BEGIN TRANSACTION')
        try:
            # 获取被删除的预约记录对应的学生ID
            cursor.execute('SELECT student_id FROM balance_record WHERE appointment_id = ?', (appointment_id,))
            student_row = cursor.fetchone()
            student_id = student_row[0] if student_row else None
            
            # 删除余额记录
            cursor.execute('DELETE FROM balance_record WHERE appointment_id = ?', (appointment_id,))
            
            # 删除预约记录
            cursor.execute('DELETE FROM appointment WHERE appointment_id = ?', (appointment_id,))
            deleted = cursor.rowcount > 0
            
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
            return deleted
        except Exception as e:
            # 回滚事务
            conn.rollback()
            raise e
        finally:
            conn.close()