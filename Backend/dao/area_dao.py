from typing import List, Optional, Dict
from Backend.db.connection import connection, transaction


class AreaDAO:
    @staticmethod
    def create(name: str) -> int:
        with transaction() as conn:
            return conn.execute('INSERT INTO area (name) VALUES (?)', (name,)).lastrowid

    @staticmethod
    def get_by_id(area_id: int) -> Optional[Dict]:
        with connection() as conn:
            row = conn.execute('SELECT * FROM area WHERE area_id = ?', (area_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all() -> List[Dict]:
        with connection() as conn:
            rows = conn.execute('SELECT * FROM area ORDER BY area_id').fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def update(area_id: int, name: str) -> bool:
        with transaction() as conn:
            return conn.execute(
                'UPDATE area SET name = ? WHERE area_id = ?', (name, area_id)
            ).rowcount > 0

    @staticmethod
    def delete(area_id: int) -> bool:
        """删除区域前解除引用，避免留下悬空的区域关联。"""
        with transaction() as conn:
            if not conn.execute('SELECT 1 FROM area WHERE area_id = ?', (area_id,)).fetchone():
                return False
            conn.execute('UPDATE student SET area_id = NULL WHERE area_id = ?', (area_id,))
            conn.execute('UPDATE coach SET area_id = NULL WHERE area_id = ?', (area_id,))
            conn.execute('UPDATE balance_record SET area_id = NULL WHERE area_id = ?', (area_id,))
            return conn.execute('DELETE FROM area WHERE area_id = ?', (area_id,)).rowcount > 0
