"""
将原 person 表拆分为 student / coach 两张表，并把历史数据迁移过去。

- 迁移前会先备份数据库到 drvaclaw.db.bak-<时间戳>
- 保留原 person_id 作为 student_id / coach_id，历史预约、充值、余额、审计记录仍然有效
- 可重复执行：person 表不存在或新表已有数据时不会重复拷贝
"""
import os
import shutil
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '../drvaclaw.db')
SQL_PATH = os.path.join(os.path.dirname(__file__), 'init_db.sql')


def has_table(cursor, name: str) -> bool:
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (name,))
    return cursor.fetchone() is not None


def migrate():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f'数据库不存在: {DB_PATH}')

    backup_path = f'{DB_PATH}.bak-{datetime.now().strftime("%Y%m%d%H%M%S")}'
    shutil.copyfile(DB_PATH, backup_path)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SQL_PATH, 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())

    if not has_table(cursor, 'person'):
        print('person 表不存在，无需迁移')
    else:
        cursor.execute("SELECT COUNT(*) FROM student")
        student_rows = cursor.fetchone()[0]
        if student_rows == 0:
            cursor.execute(
                'INSERT INTO student (student_id, name, phone, register_time, area_id) '
                "SELECT person_id, name, phone, register_time, area_id FROM person WHERE type = '学员'"
            )
        cursor.execute("SELECT COUNT(*) FROM coach")
        coach_rows = cursor.fetchone()[0]
        if coach_rows == 0:
            cursor.execute(
                'INSERT INTO coach (coach_id, name, phone, register_time, area_id) '
                "SELECT person_id, name, phone, register_time, area_id FROM person WHERE type = '教练'"
            )
        cursor.execute('DROP TABLE person')
        print('person 表已拆分并删除')

    conn.commit()

    cursor.execute('SELECT COUNT(*) FROM student')
    student_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM coach')
    coach_count = cursor.fetchone()[0]
    conn.close()

    print(f'迁移完成：学员 {student_count} 人，教练 {coach_count} 人')
    print(f'备份文件：{backup_path}')


if __name__ == '__main__':
    migrate()
