import sqlite3
from typing import List, Dict
from Backend.db.connection import get_connection

class RechargeDAO:
    @staticmethod
    def create(student_id: int, amount: float, course_count: int, recharge_time: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO recharge (student_id, amount, course_count, recharge_time) VALUES (?, ?, ?, ?)',
            (student_id, amount, course_count, recharge_time)
        )
        recharge_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return recharge_id

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
        cursor.execute(
            'UPDATE recharge SET student_id = ?, amount = ?, course_count = ?, recharge_time = ? WHERE recharge_id = ?',
            (student_id, amount, course_count, recharge_time, recharge_id)
        )
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows > 0

    @staticmethod
    def delete(recharge_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM recharge WHERE recharge_id = ?', (recharge_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows > 0