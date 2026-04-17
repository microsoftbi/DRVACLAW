#!/bin/bash

# 驾驶陪练系统启动脚本
# 同时启动后端服务和前端Vue3应用

echo "=========================================="
echo "   驾驶陪练小龙虾管理系统启动中..."
echo "=========================================="

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "项目根目录: $PROJECT_ROOT"

# 清理可能存在的旧进程
echo ""
echo "正在清理旧进程..."
pkill -f "uvicorn.*main:app" 2>/dev/null || true
pkill -f "vite.*--host" 2>/dev/null || true
sleep 1

# 启动后端服务
echo ""
echo "启动后端服务..."
cd "$PROJECT_ROOT/Backend"
if [ -d ".venv" ]; then
    echo "使用虚拟环境..."
    source .venv/bin/activate
fi
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload > "$PROJECT_ROOT/backend.log" 2>&1 &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID, 端口: 8002)"
echo "后端日志: $PROJECT_ROOT/backend.log"

# 等待后端启动
echo ""
echo "等待后端服务启动..."
sleep 3

# 启动前端服务
echo ""
echo "启动前端服务..."
cd "$PROJECT_ROOT/Frontend"
nohup npm run dev > "$PROJECT_ROOT/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "前端服务已启动 (PID: $FRONTEND_PID)"
echo "前端日志: $PROJECT_ROOT/frontend.log"

# 保存PID到文件
echo $BACKEND_PID > "$PROJECT_ROOT/backend.pid"
echo $FRONTEND_PID > "$PROJECT_ROOT/frontend.pid"

# 等待一下让服务完全启动
sleep 2

echo ""
echo "=========================================="
echo "   系统启动完成！"
echo "=========================================="
echo ""
echo "后端API地址: http://localhost:8002"
echo "前端地址: http://localhost:5173"
echo ""
echo "查看后端日志: tail -f $PROJECT_ROOT/backend.log"
echo "查看前端日志: tail -f $PROJECT_ROOT/frontend.log"
echo ""
echo "停止服务: ./stop.sh"
echo "=========================================="
