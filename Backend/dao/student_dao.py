from typing import List, Optional, Dict
from Backend.db.connection import connection, transaction


def _ensure_area(conn, area_id: Optional[int]) -> None:
    if area_id is None:
        return
    if not conn.execute('SELECT 1 FROM area WHERE area_id = ?', (area_id,)).fetchone():
        raise ValueError("区域不存在")


class StudentDAO:
    @staticmethod
    def create(name: str, phone: str, register_time: str, area_id: Optional[int],
               driving_years: Optional[int], remark: Optional[str]) -> int:
        with transaction() as conn:
            _ensure_area(conn, area_id)
            return conn.execute(
                'INSERT INTO student (name, phone, register_time, area_id, driving_years, remark) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (name, phone, register_time, area_id, driving_years or 0, remark)
            ).lastrowid

    @staticmethod
    def get_by_id(student_id: int) -> Optional[Dict]:
        with connection() as conn:
            row = conn.execute('SELECT * FROM student WHERE student_id = ?', (student_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_phone(phone: str) -> Optional[Dict]:
        with connection() as conn:
            row = conn.execute('SELECT * FROM student WHERE phone = ?', (phone,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        sql = 'SELECT * FROM student ORDER BY student_id'
        params: list = []
        if limit is not None:
            sql += ' LIMIT ? OFFSET ?'
            params = [limit, offset]
        with connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def update(student_id: int, name: Optional[str] = None, phone: Optional[str] = None,
               area_id: Optional[int] = None, driving_years: Optional[int] = None,
               remark: Optional[str] = None) -> bool:
        with transaction() as conn:
            updates, params = [], []
            for column, value in (
                ('name', name),
                ('phone', phone),
                ('area_id', area_id),
                ('driving_years', driving_years),
                ('remark', remark),
            ):
                if value is not None:
                    updates.append('%s = ?' % column)
                    params.append(value)

            if not updates:
                return False

            _ensure_area(conn, area_id)
            params.append(student_id)
            return conn.execute(
                'UPDATE student SET %s WHERE student_id = ?' % ', '.join(updates), params
            ).rowcount > 0

    @staticmethod
    def delete(student_id: int) -> bool:
        """级联删除学员的业务数据；审计日志保留，仅解除学员关联。"""
        with transaction() as conn:
            if not conn.execute('SELECT 1 FROM student WHERE student_id = ?', (student_id,)).fetchone():
                return False

            conn.execute('DELETE FROM balance_record WHERE student_id = ?', (student_id,))
            conn.execute('DELETE FROM appointment WHERE student_id = ?', (student_id,))
            conn.execute('DELETE FROM recharge WHERE student_id = ?', (student_id,))
            conn.execute('UPDATE audit_log SET student_id = NULL WHERE student_id = ?', (student_id,))

            return conn.execute('DELETE FROM student WHERE student_id = ?', (student_id,)).rowcount > 0
