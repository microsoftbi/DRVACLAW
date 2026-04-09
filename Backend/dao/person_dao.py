from typing import List, Optional, Dict
from Backend.db.connection import get_connection

class PersonDAO:
    @staticmethod
    def create(name: str, phone: str, register_time: str, area_id: Optional[int], person_type: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO person (name, phone, register_time, area_id, type) VALUES (?, ?, ?, ?, ?)',
            (name, phone, register_time, area_id, person_type)
        )
        conn.commit()
        person_id = cursor.lastrowid
        conn.close()
        return person_id
    
    @staticmethod
    def get_by_id(person_id: int) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM person WHERE person_id = ?', (person_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def get_by_phone(phone: str) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM person WHERE phone = ?', (phone,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def get_all() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM person')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_type(person_type: str) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM person WHERE type = ?', (person_type,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_students() -> List[Dict]:
        return PersonDAO.get_by_type('学员')
    
    @staticmethod
    def get_coaches() -> List[Dict]:
        return PersonDAO.get_by_type('教练')
    
    @staticmethod
    def update(person_id: int, name: Optional[str] = None, phone: Optional[str] = None, area_id: Optional[int] = None) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if phone is not None:
            updates.append('phone = ?')
            params.append(phone)
        if area_id is not None:
            updates.append('area_id = ?')
            params.append(area_id)
        
        if not updates:
            conn.close()
            return False
        
        params.append(person_id)
        cursor.execute(f'UPDATE person SET {", ".join(updates)} WHERE person_id = ?', params)
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated
    
    @staticmethod
    def delete(person_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM person WHERE person_id = ?', (person_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted