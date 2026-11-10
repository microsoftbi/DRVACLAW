from typing import List, Dict, Optional
from Backend.db.connection import connection, transaction
from Backend.dao.audit_log_dao import AuditLogDAO
from Backend.dao.ledger import recalc_balances


def _ensure_student(conn, student_id: int) -> int:
    row = conn.execute('SELECT area_id FROM student WHERE student_id = ?', (student_id,)).fetchone()
    if not row:
        raise ValueError("学员不存在")
    return row[0]


class RechargeDAO:
    @staticmethod
    def create(student_id: int, amount: float, course_count: int, recharge_time: str) -> int:
        with transaction() as conn:
            area_id = _ensure_student(conn, student_id)

            recharge_id = conn.execute(
                'INSERT INTO recharge (student_id, amount, course_count, recharge_time) VALUES (?, ?, ?, ?)',
                (student_id, amount, course_count, recharge_time)
            ).lastrowid

            current_balance = conn.execute(
                'SELECT SUM(hours) FROM balance_record WHERE student_id = ?', (student_id,)
            ).fetchone()[0] or 0

            conn.execute(
                'INSERT INTO balance_record (student_id, area_id, record_date, hours, balance, type, recharge_id, appointment_id) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (student_id, area_id, recharge_time or '', course_count,
                 current_balance + course_count, '充值', recharge_id, None)
            )

            AuditLogDAO.create(
                operator="系统",
                operation_type="充值",
                operation_result=f"充值成功，充值记录ID为{recharge_id}",
                student_id=student_id,
                coach_id=None,
                conn=conn
            )

            return recharge_id

    @staticmethod
    def get_by_id(recharge_id: int) -> Optional[Dict]:
        with connection() as conn:
            row = conn.execute('SELECT * FROM recharge WHERE recharge_id = ?', (recharge_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        sql = 'SELECT * FROM recharge ORDER BY recharge_id DESC'
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
                'SELECT * FROM recharge WHERE student_id = ? ORDER BY recharge_id DESC', (student_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def update(recharge_id: int, student_id: Optional[int] = None, amount: Optional[float] = None,
               course_count: Optional[int] = None, recharge_time: Optional[str] = None) -> bool:
        with transaction() as conn:
            old = conn.execute('SELECT * FROM recharge WHERE recharge_id = ?', (recharge_id,)).fetchone()
            if not old:
                return False

            new_student_id = student_id if student_id is not None else old['student_id']
            new_amount = amount if amount is not None else old['amount']
            new_course_count = course_count if course_count is not None else old['course_count']
            new_recharge_time = recharge_time if recharge_time is not None else old['recharge_time']

            area_id = _ensure_student(conn, new_student_id)

            conn.execute(
                'UPDATE recharge SET student_id = ?, amount = ?, course_count = ?, recharge_time = ? WHERE recharge_id = ?',
                (new_student_id, new_amount, new_course_count, new_recharge_time, recharge_id)
            )

            conn.execute(
                'UPDATE balance_record SET student_id = ?, area_id = ?, record_date = ?, hours = ? WHERE recharge_id = ?',
                (new_student_id, area_id, new_recharge_time or '', new_course_count, recharge_id)
            )

            # 学员可能被改变，新旧学员的结余都需要重算
            recalc_balances(conn, new_student_id)
            if old['student_id'] != new_student_id:
                recalc_balances(conn, old['student_id'])

            AuditLogDAO.create(
                operator="系统",
                operation_type="修改充值",
                operation_result=f"修改充值成功，充值记录ID为{recharge_id}",
                student_id=new_student_id,
                coach_id=None,
                conn=conn
            )

            return True

    @staticmethod
    def delete(recharge_id: int) -> bool:
        with transaction() as conn:
            old = conn.execute('SELECT student_id FROM recharge WHERE recharge_id = ?', (recharge_id,)).fetchone()
            if not old:
                return False
            student_id = old[0]

            conn.execute('DELETE FROM balance_record WHERE recharge_id = ?', (recharge_id,))
            conn.execute('DELETE FROM recharge WHERE recharge_id = ?', (recharge_id,))
            recalc_balances(conn, student_id)

            AuditLogDAO.create(
                operator="系统",
                operation_type="删除充值",
                operation_result=f"删除充值成功，充值记录ID为{recharge_id}",
                student_id=student_id,
                coach_id=None,
                conn=conn
            )

            return True
