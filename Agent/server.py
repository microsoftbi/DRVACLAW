"""AI 助理服务：FastAPI + SSE + deepagents 会话。监听 8003。"""

import json
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command
from pydantic import BaseModel

import config as app_config
from agent_factory import DB_PATH, build_graph

MODEL_ERROR = "尚未配置大模型，请在左侧「设置」中填写 Base URL、API Key 与模型名。"


class ChatBody(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ApproveBody(BaseModel):
    thread_id: str
    approve: bool = True
    message: Optional[str] = None


class ConfigBody(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None


checkpointer: Optional[AsyncSqliteSaver] = None
checkpointer_cm = None
_graph_cache: dict = {}


def get_graph():
    cfg = app_config.load_config()
    key = (cfg["base_url"], cfg["api_key"], cfg["model"])
    if key not in _graph_cache:
        _graph_cache.clear()
        _graph_cache[key] = build_graph(cfg, checkpointer)
    return _graph_cache[key]


@asynccontextmanager
async def lifespan(_: FastAPI):
    global checkpointer, checkpointer_cm
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    checkpointer_cm = AsyncSqliteSaver.from_conn_string(str(DB_PATH))
    checkpointer = await checkpointer_cm.__aenter__()
    yield
    await checkpointer_cm.__aexit__(None, None, None)


app = FastAPI(title="驾驶智陪工作台 · AI 助理", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def _text_of(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text") or "")
        return "".join(parts)
    return ""


def _serialize_interrupt(value: Any) -> dict:
    if not isinstance(value, dict):
        return {"action_requests": [], "raw": str(value)}
    requests = []
    for item in value.get("action_requests", []) or []:
        requests.append(
            {
                "name": item.get("name"),
                "args": item.get("args"),
                "description": item.get("description"),
            }
        )
    return {"action_requests": requests}


def _pending_from_state(state) -> Optional[dict]:
    for task in getattr(state, "tasks", ()) or ():
        interrupts = getattr(task, "interrupts", ()) or ()
        for intr in interrupts:
            value = getattr(intr, "value", intr)
            return _serialize_interrupt(value)
    return None


async def _stream(graph, inputs, config, emit_tool_events=True):
    """把 langgraph 事件翻译成前端可消费的 SSE 事件。"""
    seen_calls: set = set()
    async for mode, chunk in graph.astream(inputs, config, stream_mode=["messages", "updates"]):
        if mode == "messages":
            message, metadata = chunk
            if emit_tool_events and isinstance(message, AIMessageChunk):
                for call in getattr(message, "tool_call_chunks", []) or []:
                    call_id = call.get("id")
                    name = call.get("name")
                    if name and call_id and call_id not in seen_calls:
                        seen_calls.add(call_id)
                        yield sse("tool_start", {"name": name, "args": call.get("args") or ""})
            text = _text_of(message)
            if text and isinstance(message, (AIMessageChunk, AIMessage)):
                yield sse("token", {"text": text})
            if isinstance(message, ToolMessage):
                yield sse(
                    "tool_end",
                    {"name": getattr(message, "name", ""), "status": getattr(message, "status", "success")},
                )
        elif mode == "updates":
            for node, update in chunk.items():
                if node == "__interrupt__":
                    payload = None
                    for intr in update or ():
                        payload = _serialize_interrupt(getattr(intr, "value", intr))
                        break
                    if payload:
                        yield sse("approval_required", payload)
                        return


@app.get("/health")
async def health():
    cfg = app_config.load_config()
    return {"ok": True, "model_ready": app_config.is_ready(cfg), "backend": "http://127.0.0.1:8002"}


@app.get("/config")
async def get_config():
    return app_config.masked(app_config.load_config())


@app.put("/config")
async def put_config(body: ConfigBody):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    if not payload:
        return app_config.masked(app_config.load_config())
    # api_key 传空字符串表示清空；前端未改动时不传该字段
    app_config.save_config(payload)
    _graph_cache.clear()
    return app_config.masked(app_config.load_config())


@app.post("/config/test")
async def test_config():
    cfg = app_config.load_config()
    if not app_config.is_ready(cfg):
        return {"ok": False, "message": MODEL_ERROR}
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=cfg["model"],
            base_url=cfg["base_url"],
            api_key=cfg["api_key"],
            temperature=0,
            timeout=30,
            max_retries=0,
        )
        reply = await llm.ainvoke([HumanMessage(content="只回复 OK")])
        return {"ok": True, "message": f"连接成功：{_text_of(reply)[:80] or 'OK'}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "message": f"连接失败：{type(exc).__name__} {exc}"}


@app.post("/session")
async def new_session():
    return {"thread_id": str(uuid.uuid4())}


@app.get("/history")
async def history(thread_id: str):
    cfg = app_config.load_config()
    if not app_config.is_ready(cfg):
        return {"thread_id": thread_id, "messages": [], "pending": None}
    graph = get_graph()
    state = await graph.aget_state({"configurable": {"thread_id": thread_id}})
    messages = []
    for message in (state.values or {}).get("messages", []) or []:
        text = _text_of(message).strip()
        if not text:
            continue
        if isinstance(message, HumanMessage):
            messages.append({"role": "user", "content": text})
        elif isinstance(message, AIMessage) and not getattr(message, "tool_calls", None):
            messages.append({"role": "assistant", "content": text})
    return {"thread_id": thread_id, "messages": messages, "pending": _pending_from_state(state)}


@app.post("/chat")
async def chat(body: ChatBody):
    cfg = app_config.load_config()
    thread_id = body.thread_id or str(uuid.uuid4())

    async def gen():
        yield sse("meta", {"thread_id": thread_id})
        if not app_config.is_ready(cfg):
            yield sse("error", {"message": MODEL_ERROR, "code": "model_not_ready"})
            return
        if not body.message.strip():
            yield sse("error", {"message": "消息不能为空。"})
            return
        graph = get_graph()
        config = {"configurable": {"thread_id": thread_id}}
        try:
            async for event in _stream(
                graph, {"messages": [{"role": "user", "content": body.message}]}, config
            ):
                yield event
            yield sse("done", {"thread_id": thread_id})
        except Exception as exc:  # noqa: BLE001
            yield sse("error", {"message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/approve")
async def approve(body: ApproveBody):
    cfg = app_config.load_config()

    async def gen():
        if not app_config.is_ready(cfg):
            yield sse("error", {"message": MODEL_ERROR, "code": "model_not_ready"})
            return
        graph = get_graph()
        config = {"configurable": {"thread_id": body.thread_id}}
        try:
            state = await graph.aget_state(config)
            pending = _pending_from_state(state) or {}
            count = len(pending.get("action_requests") or [])
            if body.approve:
                decisions = [{"type": "approve"} for _ in range(max(count, 1))]
            else:
                reason = body.message or "管理员拒绝执行该操作。"
                decisions = [{"type": "reject", "message": reason} for _ in range(max(count, 1))]
            async for event in _stream(graph, Command(resume={"decisions": decisions}), config):
                yield event
            yield sse("done", {"thread_id": body.thread_id})
        except Exception as exc:  # noqa: BLE001
            yield sse("error", {"message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
