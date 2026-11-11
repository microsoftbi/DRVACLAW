#!/bin/bash

# 驾驶陪练系统启动脚本
# 同时启动后端服务和前端Vue3应用

echo "=========================================="
echo "   驾驶智陪工作台启动中..."
echo "=========================================="

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "项目根目录: $PROJECT_ROOT"

# 清理可能存在的旧进程
echo ""
echo "正在清理旧进程..."
pkill -f "uvicorn.*main:app" 2>/dev/null || true
pkill -f "uvicorn.*server:app" 2>/dev/null || true
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

# 启动 AI 助理服务
echo ""
echo "启动 AI 助理服务..."
cd "$PROJECT_ROOT/Agent"
if [ ! -x ".venv/bin/python" ]; then
    echo "未找到 Agent 运行环境，请先执行 Agent 安装步骤"
else
    nohup .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8003 > "$PROJECT_ROOT/agent.log" 2>&1 &
    AGENT_PID=$!
    echo "AI 助理服务已启动 (PID: $AGENT_PID, 端口: 8003)"
    echo "AI 助理日志: $PROJECT_ROOT/agent.log"
    echo $AGENT_PID > "$PROJECT_ROOT/agent.pid"
fi

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
echo "AI 助理地址: http://localhost:8003"
echo "前端地址: http://localhost:5174"
echo ""
echo "查看后端日志: tail -f $PROJECT_ROOT/backend.log"
echo "查看 AI 助理日志: tail -f $PROJECT_ROOT/agent.log"
echo "查看前端日志: tail -f $PROJECT_ROOT/frontend.log"
echo ""
echo "停止服务: ./stop.sh"
echo "=========================================="
