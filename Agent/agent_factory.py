"""构建 deepagents 图：装载 SKILLS 技能、业务工具与会话检查点。"""

import re
from pathlib import Path

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

from config import DATA_DIR
from tools import ALL_TOOLS, WRITE_TOOLS

ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "SKILLS" / "SKILL.md"
DB_PATH = DATA_DIR / "agent.sqlite"

SYSTEM_PROMPT = """你是「驾驶智陪工作台」内置的 AI 助理，服务于驾校陪练业务的管理员。

工作要求：
1. 优先调用工具获取真实数据，禁止编造学员、教练、车辆、预约、充值等业务数据。
2. 用户提到「老赵」时，视为启用了下面的《老赵 · 驾驶智陪工作台 API 技能》，按其路由表选择接口。
3. 查询类工具可直接调用；新增/修改/删除类工具会触发人工审批，用户确认后才真正写入。
   调用写工具前，先用一句话说明你准备做什么；被拒绝时不要重试，改为询问用户。
4. 用户描述不完整时（如缺少日期、手机号、区域），先追问必要信息，不要猜。
5. 回答使用简洁的中文，数据用 Markdown 表格或列表呈现；金额保留两位小数；时间用 YYYY-MM-DD。
6. 工具返回 JSON，若含 error 字段，请把错误原因翻译成业务语言告诉用户，并给出下一步建议。
7. 系统能力覆盖：区域、学员、教练、车辆、预约、充值、余额、操作审计、区域统计。
"""


def _load_skill_text() -> str:
    if not SKILL_PATH.exists():
        return ""
    raw = SKILL_PATH.read_text(encoding="utf-8")
    # 去掉 YAML frontmatter，只保留正文
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", raw, count=1, flags=re.S)
    return body.strip()


def build_graph(config: dict, checkpointer):
    llm = ChatOpenAI(
        model=config["model"],
        base_url=config["base_url"],
        api_key=config["api_key"],
        temperature=0.2,
        timeout=120,
        max_retries=1,
    )
    skill_text = _load_skill_text()
    prompt = SYSTEM_PROMPT
    if skill_text:
        prompt += "\n\n===== 技能文档开始 =====\n" + skill_text + "\n===== 技能文档结束 ====="

    interrupt_on = {tool.name: True for tool in WRITE_TOOLS}
    return create_deep_agent(
        model=llm,
        tools=ALL_TOOLS,
        system_prompt=prompt,
        interrupt_on=interrupt_on,
        checkpointer=checkpointer,
    )
