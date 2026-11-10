import sqlite3
import os
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../drvaclaw.db')


def get_connection():
    # timeout: 写锁冲突时最多等待 30s，避免直接抛 "database is locked"
    # isolation_level=None: 自动提交模式，由 transaction() 显式控制事务边界
    conn = sqlite3.connect(DATABASE_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    # 开启外键约束，保证引用完整性（每个连接都需要设置）
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


@contextmanager
def connection():
    """只读场景：自动关闭连接，避免异常路径漏掉 close()。"""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction():
    """写场景：BEGIN IMMEDIATE 立即获取写锁，保证“读-改-写”原子性，异常自动回滚。"""
    conn = get_connection()
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield conn
        conn.execute('COMMIT')
    except Exception:
        conn.execute('ROLLBACK')
        raise
    finally:
        conn.close()
