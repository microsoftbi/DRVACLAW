import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../drvaclaw.db')

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 从init_db.sql文件中读取建表脚本
    sql_file_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        create_tables_sql = f.read()
    
    # 执行建表语句
    cursor.executescript(create_tables_sql)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('数据库初始化完成')

