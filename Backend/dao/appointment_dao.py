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
        cursor.execute('SELECT * FROM appointment')
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
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated
    
    @staticmethod
    def delete(appointment_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM appointment WHERE appointment_id = ?', (appointment_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted