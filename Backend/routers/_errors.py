import sqlite3
from fastapi import HTTPException


def http_error(exc: Exception) -> HTTPException:
    """把内部异常映射为对外的 HTTP 语义，避免泄露 SQL/堆栈细节。"""
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, sqlite3.IntegrityError):
        return HTTPException(status_code=400, detail="数据校验失败：唯一性或关联约束不满足")
    if isinstance(exc, sqlite3.OperationalError):
        return HTTPException(status_code=500, detail="数据库操作失败")
    return HTTPException(status_code=500, detail="服务器内部错误")
