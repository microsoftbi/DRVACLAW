import datetime
from typing import List, Optional, Dict
from Backend.db.connection import connection, transaction
from Backend.dao.audit_log_dao import AuditLogDAO
from Backend.dao.ledger import recalc_balances

APPOINTMENT_STATUSES = ('待确认', '已确认', '已取消', '已完成')


def _validate_times(start_time: int, end_time: int) -> None:
    if not (1 <= start_time <= 24 and 1 <= end_time <= 24):
        raise ValueError("预约时段不合法：时间须在 1-24 之间")
    if start_time >= end_time:
        raise ValueError("预约时段不合法：结束时间须晚于开始时间")


def _validate_status(status: str) -> None:
    if status not in APPOINTMENT_STATUSES:
        raise ValueError("预约状态不合法：%s" % status)


def _ensure_refs(conn, student_id: int, coach_id: int) -> None:
    if not conn.execute('SELECT 1 FROM student WHERE student_id = ?', (student_id,)).fetchone():
        raise ValueError("学员不存在")
    if not conn.execute('SELECT 1 FROM coach WHERE coach_id = ?', (coach_id,)).fetchone():
        raise ValueError("教练不存在")


def _write_consumption(conn, appointment_id: int, student_id: int, start_time: int, end_time: int) -> None:
    """按预约当前时段写入一条课时消耗记录（先清理旧记录，保证幂等）。"""
    conn.execute(
        'DELETE FROM balance_record WHERE appointment_id = ? AND type = ?',
        (appointment_id, '课时消耗')
    )

    student = conn.execute('SELECT area_id FROM student WHERE student_id = ?', (student_id,)).fetchone()
    area_id = student[0] if student else None

    current_balance = conn.execute(
        'SELECT SUM(hours) FROM balance_record WHERE student_id = ?', (student_id,)
    ).fetchone()[0] or 0

    hours = -(end_time - start_time)
    record_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        'INSERT INTO balance_record (student_id, area_id, record_date, hours, balance, type, recharge_id, appointment_id) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (student_id, area_id, record_date, hours, current_balance + hours, '课时消耗', None, appointment_id)
    )
    recalc_balances(conn, student_id)


def _remove_consumption(conn, appointment_id: int, student_id: int) -> None:
    """撤销预约产生的课时消耗记录并重算结余。"""
    conn.execute(
        'DELETE FROM balance_record WHERE appointment_id = ? AND type = ?',
        (appointment_id, '课时消耗')
    )
    recalc_balances(conn, student_id)


class AppointmentDAO:
    @staticmethod
    def create(student_id: int, coach_id: int, appointment_date: str,
               start_time: int, end_time: int, status: str) -> int:
        _validate_status(status)
        _validate_times(start_time, end_time)

        with transaction() as conn:
            _ensure_refs(conn, student_id, coach_id)

            appointment_id = conn.execute(
                'INSERT INTO appointment (student_id, coach_id, appointment_date, start_time, end_time, status) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (student_id, coach_id, appointment_date, start_time, end_time, status)
            ).lastrowid

            AuditLogDAO.create(
                operator="系统",
                operation_type="创建预约课程",
                operation_result=f"课程创建成功，课程预约ID为{appointment_id}",
                student_id=student_id,
                coach_id=coach_id,
                conn=conn
            )

            return appointment_id

    @staticmethod
    def get_by_id(appointment_id: int) -> Optional[Dict]:
        with connection() as conn:
            row = conn.execute('SELECT * FROM appointment WHERE appointment_id = ?', (appointment_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        sql = 'SELECT * FROM appointment ORDER BY appointment_id DESC'
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
                'SELECT * FROM appointment WHERE student_id = ? ORDER BY appointment_id DESC', (student_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_coach_id(coach_id: int) -> List[Dict]:
        with connection() as conn:
            rows = conn.execute(
                'SELECT * FROM appointment WHERE coach_id = ? ORDER BY appointment_id DESC', (coach_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_date(appointment_date: str) -> List[Dict]:
        with connection() as conn:
            rows = conn.execute(
                'SELECT * FROM appointment WHERE appointment_date = ?', (appointment_date,)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def update(appointment_id: int, student_id: Optional[int] = None, coach_id: Optional[int] = None,
               appointment_date: Optional[str] = None, start_time: Optional[int] = None,
               end_time: Optional[int] = None, status: Optional[str] = None) -> bool:
        with transaction() as conn:
            old = conn.execute('SELECT * FROM appointment WHERE appointment_id = ?', (appointment_id,)).fetchone()
            if not old:
                return False

            old_status = old['status']
            new_student_id = student_id if student_id is not None else old['student_id']
            new_coach_id = coach_id if coach_id is not None else old['coach_id']
            new_start = start_time if start_time is not None else old['start_time']
            new_end = end_time if end_time is not None else old['end_time']
            new_status = status if status is not None else old_status

            if status is not None:
                _validate_status(new_status)
            _validate_times(new_start, new_end)
            if student_id is not None or coach_id is not None:
                _ensure_refs(conn, new_student_id, new_coach_id)

            updates, params = [], []
            for column, value in (
                ('student_id', student_id),
                ('coach_id', coach_id),
                ('appointment_date', appointment_date),
                ('start_time', start_time),
                ('end_time', end_time),
                ('status', status),
            ):
                if value is not None:
                    updates.append('%s = ?' % column)
                    params.append(value)

            if not updates:
                return False

            params.append(appointment_id)
            updated = conn.execute(
                'UPDATE appointment SET %s WHERE appointment_id = ?' % ', '.join(updates), params
            ).rowcount > 0

            # 课时记录随预约状态保持幂等：完成时写入/刷新，回退或取消时撤销
            if new_status == '已完成':
                _write_consumption(conn, appointment_id, new_student_id, new_start, new_end)
            else:
                _remove_consumption(conn, appointment_id, new_student_id)

            if updated:
                operation_type = "修改预约课程"
                operation_result = f"修改预约课程成功，课程预约ID为{appointment_id}"
                if status is not None and status != old_status:
                    if status == "已确认":
                        operation_type = "确认预约课程"
                        operation_result = f"确认预约课程成功，课程预约ID为{appointment_id}"
                    elif status == "已取消":
                        operation_type = "取消预约课程"
                        operation_result = f"取消预约课程成功，课程预约ID为{appointment_id}"
                    elif status == "已完成":
                        operation_type = "标记预约课程为已完成"
                        operation_result = f"标记预约课程为已完成，课程预约ID为{appointment_id}"

                AuditLogDAO.create(
                    operator="系统",
                    operation_type=operation_type,
                    operation_result=operation_result,
                    student_id=new_student_id,
                    coach_id=new_coach_id,
                    conn=conn
                )

            return updated

    @staticmethod
    def delete(appointment_id: int) -> bool:
        with transaction() as conn:
            old = conn.execute(
                'SELECT student_id, coach_id FROM appointment WHERE appointment_id = ?', (appointment_id,)
            ).fetchone()
            if not old:
                return False

            student_id, coach_id = old[0], old[1]

            conn.execute('DELETE FROM balance_record WHERE appointment_id = ?', (appointment_id,))
            deleted = conn.execute(
                'DELETE FROM appointment WHERE appointment_id = ?', (appointment_id,)
            ).rowcount > 0
            recalc_balances(conn, student_id)

            AuditLogDAO.create(
                operator="系统",
                operation_type="删除预约课程",
                operation_result=f"删除预约课程成功，课程预约ID为{appointment_id}",
                student_id=student_id,
                coach_id=coach_id,
                conn=conn
            )

            return deleted
