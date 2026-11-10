import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../drvaclaw.db')
SQL_FILE_PATH = os.path.join(os.path.dirname(__file__), 'init_db.sql')

# 旧版本建表脚本错误地把外键指向了已不存在的 person 表，
# 开启外键约束前需要把这些表重建为指向 student/coach 的正确结构。
LEGACY_FK_TABLES = ('appointment', 'recharge', 'balance_record', 'audit_log')


def _has_legacy_foreign_keys(conn) -> bool:
    for table in LEGACY_FK_TABLES:
        for row in conn.execute('PRAGMA foreign_key_list(%s)' % table):
            if row[2] == 'person':
                return True
    return False


def _migrate_legacy_schema(conn) -> None:
    if not _has_legacy_foreign_keys(conn):
        return

    conn.execute('PRAGMA foreign_keys = OFF')

    columns = {
        table: [row[1] for row in conn.execute('PRAGMA table_info(%s)' % table)]
        for table in LEGACY_FK_TABLES
    }

    for table in LEGACY_FK_TABLES:
        conn.execute('ALTER TABLE %s RENAME TO %s__legacy' % (table, table))

    with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())

    for table in LEGACY_FK_TABLES:
        column_list = ', '.join(columns[table])
        conn.execute(
            'INSERT INTO %s (%s) SELECT %s FROM %s__legacy' % (table, column_list, column_list, table)
        )
        conn.execute('DROP TABLE %s__legacy' % table)

    # 修复历史遗留的悬空引用，保证开启外键后数据自洽
    conn.execute(
        'UPDATE audit_log SET student_id = NULL '
        'WHERE student_id IS NOT NULL AND student_id NOT IN (SELECT student_id FROM student)'
    )
    conn.execute(
        'UPDATE audit_log SET coach_id = NULL '
        'WHERE coach_id IS NOT NULL AND coach_id NOT IN (SELECT coach_id FROM coach)'
    )
    conn.commit()


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        _migrate_legacy_schema(conn)

        with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())

        conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    print('数据库初始化完成')
