"""配置管理

优先级链（从高到低）：
1. 函数参数 api_key=
2. 环境变量 ZHIPU_API_KEY
3. 配置文件 ~/.config/zhipu-free/config.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "zhipu-free"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def _save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    CONFIG_FILE.chmod(0o600)


def get_api_key(api_key: str | None = None) -> str:
    """按优先级链获取 API Key

    1. 显式传入的 api_key 参数
    2. 环境变量 ZHIPU_API_KEY
    3. 配置文件 ~/.config/zhipu-free/config.json
    """
    if api_key:
        return api_key
    env_key = os.environ.get("ZHIPU_API_KEY", "")
    if env_key:
        return env_key
    config = _load_config()
    return config.get("api_key", "")


def set_api_key(api_key: str) -> None:
    """将 API Key 保存到配置文件"""
    config = _load_config()
    config["api_key"] = api_key
    _save_config(config)


def get_config() -> dict:
    """获取完整配置"""
    return _load_config()


def clear_api_key() -> None:
    """清除已保存的 API Key"""
    config = _load_config()
    config.pop("api_key", None)
    _save_config(config)
