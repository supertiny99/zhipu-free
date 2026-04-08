"""数据模型定义"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FreeModel(str, Enum):
    """智谱免费模型枚举"""

    # 文本对话
    GLM_4_7_FLASH = "glm-4.7-flash"
    GLM_4_FLASH = "glm-4-flash-250414"

    # 多模态理解
    GLM_4_6V_FLASH = "glm-4.6v-flash"
    GLM_4_1V_THINKING = "glm-4.1v-thinking-flash"
    GLM_4V_FLASH = "glm-4v-flash"

    # 图片生成
    COGVIEW_3_FLASH = "cogview-3-flash"

    # 视频生成
    COGVIDEOX_FLASH = "cogvideox-flash"


# ── 消息构造 ────────────────────────────────────────────


@dataclass
class ImageUrl:
    url: str  # HTTP URL 或 Base64

    def to_dict(self) -> dict:
        return {"type": "image_url", "image_url": {"url": self.url}}


@dataclass
class VideoUrl:
    url: str

    def to_dict(self) -> dict:
        return {"type": "video_url", "video_url": {"url": self.url}}


@dataclass
class FileUrl:
    url: str

    def to_dict(self) -> dict:
        return {"type": "file_url", "file_url": {"url": self.url}}


@dataclass
class ContentPart:
    """多模态内容片段，可以是文本、图片、视频或文件"""

    text: str | None = None
    image: ImageUrl | None = None
    video: VideoUrl | None = None
    file: FileUrl | None = None

    def to_dict(self) -> dict:
        if self.text is not None:
            return {"type": "text", "text": self.text}
        if self.image is not None:
            return self.image.to_dict()
        if self.video is not None:
            return self.video.to_dict()
        if self.file is not None:
            return self.file.to_dict()
        raise ValueError("ContentPart 至少需要一个非空字段")


@dataclass
class ChatMessage:
    role: str  # user / assistant / system
    content: str | list[ContentPart]

    def to_dict(self) -> dict:
        if isinstance(self.content, str):
            return {"role": self.role, "content": self.content}
        return {
            "role": self.role,
            "content": [p.to_dict() for p in self.content],
        }


@dataclass
class ThinkingConfig:
    """思考模式配置"""

    enabled: bool = True
    budget_tokens: int | None = None  # 预留思考 token（可选）

    def to_dict(self) -> dict | None:
        if not self.enabled:
            return {"type": "disabled"}
        d: dict[str, Any] = {"type": "enabled"}
        if self.budget_tokens:
            d["budget_tokens"] = self.budget_tokens
        return d


@dataclass
class Tool:
    """Function Call 工具定义"""

    type: str = "function"
    function: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"type": self.type, "function": self.function}
