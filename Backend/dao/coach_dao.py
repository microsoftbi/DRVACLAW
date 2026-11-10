from typing import List, Optional, Dict
from Backend.db.connection import connection, transaction
from Backend.dao.ledger import recalc_balances


def _ensure_area(conn, area_id: Optional[int]) -> None:
    if area_id is None:
        return
    if not conn.execute('SELECT 1 FROM area WHERE area_id = ?', (area_id,)).fetchone():
        raise ValueError("区域不存在")


def _ensure_vehicles(conn, vehicle_ids: List[int]) -> None:
    if not vehicle_ids:
        return
    placeholders = ', '.join('?' * len(vehicle_ids))
    found = conn.execute(
        'SELECT COUNT(*) FROM vehicle WHERE vehicle_id IN (%s)' % placeholders, vehicle_ids
    ).fetchone()[0]
    if found != len(set(vehicle_ids)):
        raise ValueError("车辆不存在")


class CoachDAO:
    @staticmethod
    def create(name: str, phone: str, register_time: str, area_id: Optional[int],
               vehicle_ids: Optional[List[int]]) -> int:
        with transaction() as conn:
            _ensure_area(conn, area_id)
            _ensure_vehicles(conn, vehicle_ids or [])

            coach_id = conn.execute(
                'INSERT INTO coach (name, phone, register_time, area_id) VALUES (?, ?, ?, ?)',
                (name, phone, register_time, area_id)
            ).lastrowid

            for vehicle_id in vehicle_ids or []:
                conn.execute(
                    'INSERT OR IGNORE INTO coach_vehicle (coach_id, vehicle_id) VALUES (?, ?)',
                    (coach_id, vehicle_id)
                )

            return coach_id

    @staticmethod
    def get_by_id(coach_id: int) -> Optional[Dict]:
        with connection() as conn:
            row = conn.execute('SELECT * FROM coach WHERE coach_id = ?', (coach_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        sql = 'SELECT * FROM coach ORDER BY coach_id'
        params: list = []
        if limit is not None:
            sql += ' LIMIT ? OFFSET ?'
            params = [limit, offset]
        with connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_all_with_vehicles(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """一次性批量取车辆关联，避免逐个教练查询造成 N+1。"""
        sql = 'SELECT * FROM coach ORDER BY coach_id'
        params: list = []
        if limit is not None:
            sql += ' LIMIT ? OFFSET ?'
            params = [limit, offset]

        with connection() as conn:
            coaches = [dict(row) for row in conn.execute(sql, params).fetchall()]
            if coaches:
                coach_ids = [c['coach_id'] for c in coaches]
                placeholders = ', '.join('?' * len(coach_ids))
                links = conn.execute(
                    'SELECT coach_id, vehicle_id FROM coach_vehicle WHERE coach_id IN (%s)' % placeholders,
                    coach_ids
                ).fetchall()
                mapping: Dict[int, List[int]] = {cid: [] for cid in coach_ids}
                for link in links:
                    mapping[link['coach_id']].append(link['vehicle_id'])
                for coach in coaches:
                    coach['vehicle_ids'] = mapping[coach['coach_id']]

        return coaches

    @staticmethod
    def get_vehicle_ids(coach_id: int) -> List[int]:
        with connection() as conn:
            rows = conn.execute(
                'SELECT vehicle_id FROM coach_vehicle WHERE coach_id = ?', (coach_id,)
            ).fetchall()
            return [row[0] for row in rows]

    @staticmethod
    def get_vehicles(coach_id: int) -> List[Dict]:
        with connection() as conn:
            rows = conn.execute(
                'SELECT v.* FROM vehicle v JOIN coach_vehicle cv ON v.vehicle_id = cv.vehicle_id '
                'WHERE cv.coach_id = ?', (coach_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def update(coach_id: int, name: Optional[str] = None, phone: Optional[str] = None,
               area_id: Optional[int] = None) -> bool:
        with transaction() as conn:
            if not conn.execute('SELECT 1 FROM coach WHERE coach_id = ?', (coach_id,)).fetchone():
                return False

            _ensure_area(conn, area_id)

            updates, params = [], []
            for column, value in (('name', name), ('phone', phone), ('area_id', area_id)):
                if value is not None:
                    updates.append('%s = ?' % column)
                    params.append(value)

            if not updates:
                return False

            params.append(coach_id)
            return conn.execute(
                'UPDATE coach SET %s WHERE coach_id = ?' % ', '.join(updates), params
            ).rowcount > 0

    @staticmethod
    def set_vehicles(coach_id: int, vehicle_ids: List[int]) -> None:
        with transaction() as conn:
            if not conn.execute('SELECT 1 FROM coach WHERE coach_id = ?', (coach_id,)).fetchone():
                raise ValueError("教练不存在")

            _ensure_vehicles(conn, vehicle_ids or [])
            conn.execute('DELETE FROM coach_vehicle WHERE coach_id = ?', (coach_id,))
            for vehicle_id in vehicle_ids or []:
                conn.execute(
                    'INSERT OR IGNORE INTO coach_vehicle (coach_id, vehicle_id) VALUES (?, ?)',
                    (coach_id, vehicle_id)
                )

    @staticmethod
    def delete(coach_id: int) -> bool:
        """级联删除教练的预约与关联数据；审计日志保留，仅解除教练关联。"""
        with transaction() as conn:
            if not conn.execute('SELECT 1 FROM coach WHERE coach_id = ?', (coach_id,)).fetchone():
                return False

            appointment_rows = conn.execute(
                'SELECT appointment_id, student_id FROM appointment WHERE coach_id = ?', (coach_id,)
            ).fetchall()

            if appointment_rows:
                appointment_ids = [row[0] for row in appointment_rows]
                student_ids = {row[1] for row in appointment_rows}
                placeholders = ', '.join('?' * len(appointment_ids))
                conn.execute(
                    'DELETE FROM balance_record WHERE appointment_id IN (%s)' % placeholders,
                    appointment_ids
                )
                conn.execute('DELETE FROM appointment WHERE coach_id = ?', (coach_id,))
                for student_id in student_ids:
                    recalc_balances(conn, student_id)

            conn.execute('UPDATE audit_log SET coach_id = NULL WHERE coach_id = ?', (coach_id,))
            conn.execute('DELETE FROM coach_vehicle WHERE coach_id = ?', (coach_id,))
            return conn.execute('DELETE FROM coach WHERE coach_id = ?', (coach_id,)).rowcount > 0
