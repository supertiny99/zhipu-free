"""配置管理

优先级链（从高到低）：
1. 函数参数 api_key=
2. 环境变量 ZHIPU_API_KEY
3. 项目 .env 文件
4. 全局配置文件 ~/.config/zhipu-free/config.json
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


def _load_dotenv() -> dict[str, str]:
    """从当前目录向上查找 .env 文件并解析 KEY=VALUE"""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        env_file = parent / ".env"
        if env_file.is_file():
            result = {}
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                result[key] = value
            return result
    return {}


def get_api_key(api_key: str | None = None) -> str:
    """按优先级链获取 API Key

    1. 显式传入的 api_key 参数
    2. 环境变量 ZHIPU_API_KEY
    3. 项目 .env 文件中的 ZHIPU_API_KEY
    4. 全局配置文件 ~/.config/zhipu-free/config.json
    """
    if api_key:
        return api_key
    env_key = os.environ.get("ZHIPU_API_KEY", "")
    if env_key:
        return env_key
    dotenv = _load_dotenv()
    if dotenv.get("ZHIPU_API_KEY"):
        return dotenv["ZHIPU_API_KEY"]
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
