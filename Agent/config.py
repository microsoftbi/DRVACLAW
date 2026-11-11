"""Agent 服务配置读写：模型 Base URL / API Key / 模型名。"""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CONFIG_PATH = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key": "",
    "model": "",
}


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                config.update({k: v for k, v in saved.items() if k in DEFAULT_CONFIG})
        except (json.JSONDecodeError, OSError):
            pass
    # 环境变量优先，便于无界面部署
    config["base_url"] = os.environ.get("AGENT_BASE_URL") or config["base_url"]
    config["api_key"] = os.environ.get("AGENT_API_KEY") or config["api_key"]
    config["model"] = os.environ.get("AGENT_MODEL") or config["model"]
    return config


def save_config(data: dict) -> dict:
    _ensure_dir()
    config = load_config()
    for key in DEFAULT_CONFIG:
        value = data.get(key)
        if isinstance(value, str):
            config[key] = value.strip()
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        CONFIG_PATH.chmod(0o600)
    except OSError:
        pass
    return config


def is_ready(config: dict) -> bool:
    return bool(config.get("base_url") and config.get("api_key") and config.get("model"))


def masked(config: dict) -> dict:
    key = config.get("api_key") or ""
    if key:
        mask = f"{key[:4]}****{key[-4:]}" if len(key) > 10 else "****"
    else:
        mask = ""
    return {
        "base_url": config.get("base_url") or "",
        "model": config.get("model") or "",
        "api_key_set": bool(key),
        "api_key_masked": mask,
        "ready": is_ready(config),
    }
