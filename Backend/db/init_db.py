import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../drvaclaw.db')

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS area (
            area_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS person (
            person_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            register_time TEXT NOT NULL,
            area_id INTEGER,
            type TEXT NOT NULL CHECK(type IN ('学员', '教练')),
            FOREIGN KEY (area_id) REFERENCES area(area_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointment (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            coach_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            start_time INTEGER NOT NULL CHECK(start_time BETWEEN 1 AND 24),
            end_time INTEGER NOT NULL CHECK(end_time BETWEEN 1 AND 24),
            status TEXT NOT NULL CHECK(status IN ('待确认', '已确认', '已取消')),
            FOREIGN KEY (student_id) REFERENCES person(person_id),
            FOREIGN KEY (coach_id) REFERENCES person(person_id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('数据库初始化完成')
