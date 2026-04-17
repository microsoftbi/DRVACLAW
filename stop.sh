#!/bin/bash

# 驾驶陪练系统停止脚本

echo "=========================================="
echo "   正在停止驾驶陪练系统..."
echo "=========================================="

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 停止后端服务
if [ -f "$PROJECT_ROOT/backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/backend.pid" 2>/dev/null)
    if [ -n "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID 2>/dev/null
        echo "后端服务已停止 (PID: $BACKEND_PID)"
    fi
    rm -f "$PROJECT_ROOT/backend.pid"
fi

# 停止前端服务
if [ -f "$PROJECT_ROOT/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/frontend.pid" 2>/dev/null)
    if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID 2>/dev/null
        echo "前端服务已停止 (PID: $FRONTEND_PID)"
    fi
    rm -f "$PROJECT_ROOT/frontend.pid"
fi

# 额外清理可能残留的进程
pkill -f "uvicorn.*main:app" 2>/dev/null || true
pkill -f "vite.*--host" 2>/dev/null || true

# 清理日志文件（可选，保留以便查看）
# rm -f "$PROJECT_ROOT/backend.log" "$PROJECT_ROOT/frontend.log"

echo ""
echo "=========================================="
echo "   系统已停止！"
echo "=========================================="
