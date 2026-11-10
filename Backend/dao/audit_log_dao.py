from typing import List, Dict, Optional
import datetime
from Backend.db.connection import connection

class AuditLogDAO:
    @staticmethod
    def create(operator: str, operation_type: str, operation_result: str,
               student_id: int = None, coach_id: int = None, conn=None) -> int:
        """写入审计日志。

        传入 conn 时复用调用方事务，保证业务写入与审计记录同成功/同回滚；
        不传时自建连接并提交。
        """
        operation_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = ('INSERT INTO audit_log (operator, student_id, coach_id, operation_time, operation_type, operation_result) '
               'VALUES (?, ?, ?, ?, ?, ?)')
        params = (operator, student_id, coach_id, operation_time, operation_type, operation_result)

        if conn is not None:
            return conn.execute(sql, params).lastrowid

        with connection() as own_conn:
            own_conn.execute('BEGIN IMMEDIATE')
            try:
                audit_id = own_conn.execute(sql, params).lastrowid
                own_conn.execute('COMMIT')
                return audit_id
            except Exception:
                own_conn.execute('ROLLBACK')
                raise

    @staticmethod
    def get_all(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        sql = 'SELECT * FROM audit_log ORDER BY audit_id DESC'
        params: list = []
        if limit is not None:
            sql += ' LIMIT ? OFFSET ?'
            params = [limit, offset]
        with connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_student_id(student_id: int) -> List[Dict]:
        with connection() as conn:
            rows = conn.execute(
                'SELECT * FROM audit_log WHERE student_id = ? ORDER BY audit_id DESC', (student_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_coach_id(coach_id: int) -> List[Dict]:
        with connection() as conn:
            rows = conn.execute(
                'SELECT * FROM audit_log WHERE coach_id = ? ORDER BY audit_id DESC', (coach_id,)
            ).fetchall()
            return [dict(row) for row in rows]
