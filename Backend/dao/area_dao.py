from typing import List, Optional, Dict
from Backend.db.connection import get_connection

class AreaDAO:
    @staticmethod
    def create(name: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO area (name) VALUES (?)', (name,))
        conn.commit()
        area_id = cursor.lastrowid
        conn.close()
        return area_id
    
    @staticmethod
    def get_by_id(area_id: int) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM area WHERE area_id = ?', (area_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def get_all() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM area')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def update(area_id: int, name: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE area SET name = ? WHERE area_id = ?', (name, area_id))
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated
    
    @staticmethod
    def delete(area_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM area WHERE area_id = ?', (area_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
