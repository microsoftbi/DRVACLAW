from typing import List, Optional, Dict
from Backend.db.connection import connection


class BalanceRecordDAO:
    @staticmethod
    def get_all(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        sql = 'SELECT * FROM balance_record ORDER BY record_id DESC'
        params: list = []
        if limit is not None:
            sql += ' LIMIT ? OFFSET ?'
            params = [limit, offset]
        with connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(record_id: int) -> Optional[Dict]:
        with connection() as conn:
            row = conn.execute('SELECT * FROM balance_record WHERE record_id = ?', (record_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_student_id(student_id: int) -> List[Dict]:
        with connection() as conn:
            rows = conn.execute(
                'SELECT * FROM balance_record WHERE student_id = ? ORDER BY record_date DESC, record_id DESC',
                (student_id,)
            ).fetchall()
            return [dict(row) for row in rows]
