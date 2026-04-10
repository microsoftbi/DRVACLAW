from typing import List, Dict, Optional
from Backend.db.connection import get_connection

class BalanceRecordDAO:
    @staticmethod
    def create(student_id: int, area_id: Optional[int], record_date: str, hours: float, balance: float, 
               record_type: str, recharge_id: Optional[int], appointment_id: Optional[int]) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO balance_record (student_id, area_id, record_date, hours, balance, type, recharge_id, appointment_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (student_id, area_id, record_date, hours, balance, record_type, recharge_id, appointment_id)
        )
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id
    
    @staticmethod
    def get_by_id(record_id: int) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM balance_record WHERE record_id = ?', (record_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def get_all() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        # 按日期升序排序，同一天的充值记录排在前面
        cursor.execute('''
            SELECT * FROM balance_record 
            ORDER BY record_date ASC, 
                     CASE 
                         WHEN type = '充值' THEN 0 
                         ELSE 1 
                     END ASC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_student_id(student_id: int) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        # 按日期升序排序，同一天的充值记录排在前面
        cursor.execute('''
            SELECT * FROM balance_record 
            WHERE student_id = ? 
            ORDER BY record_date ASC, 
                     CASE 
                         WHEN type = '充值' THEN 0 
                         ELSE 1 
                     END ASC
        ''', (student_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def delete_by_recharge_id(recharge_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM balance_record WHERE recharge_id = ?', (recharge_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows > 0
    
    @staticmethod
    def delete_by_appointment_id(appointment_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM balance_record WHERE appointment_id = ?', (appointment_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows > 0