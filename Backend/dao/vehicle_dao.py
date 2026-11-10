from typing import List, Optional, Dict
from Backend.db.connection import connection, transaction


class VehicleDAO:
    @staticmethod
    def create(vehicle_type: str, brand: str, model: str, create_time: str) -> int:
        with transaction() as conn:
            return conn.execute(
                'INSERT INTO vehicle (vehicle_type, brand, model, create_time) VALUES (?, ?, ?, ?)',
                (vehicle_type, brand, model, create_time)
            ).lastrowid

    @staticmethod
    def get_by_id(vehicle_id: int) -> Optional[Dict]:
        with connection() as conn:
            row = conn.execute('SELECT * FROM vehicle WHERE vehicle_id = ?', (vehicle_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        sql = 'SELECT * FROM vehicle ORDER BY vehicle_id'
        params: list = []
        if limit is not None:
            sql += ' LIMIT ? OFFSET ?'
            params = [limit, offset]
        with connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def update(vehicle_id: int, vehicle_type: Optional[str] = None,
               brand: Optional[str] = None, model: Optional[str] = None) -> bool:
        with transaction() as conn:
            updates, params = [], []
            for column, value in (('vehicle_type', vehicle_type), ('brand', brand), ('model', model)):
                if value is not None:
                    updates.append('%s = ?' % column)
                    params.append(value)

            if not updates:
                return False

            params.append(vehicle_id)
            return conn.execute(
                'UPDATE vehicle SET %s WHERE vehicle_id = ?' % ', '.join(updates), params
            ).rowcount > 0

    @staticmethod
    def delete(vehicle_id: int) -> bool:
        with transaction() as conn:
            if not conn.execute('SELECT 1 FROM vehicle WHERE vehicle_id = ?', (vehicle_id,)).fetchone():
                return False
            conn.execute('DELETE FROM coach_vehicle WHERE vehicle_id = ?', (vehicle_id,))
            return conn.execute('DELETE FROM vehicle WHERE vehicle_id = ?', (vehicle_id,)).rowcount > 0
