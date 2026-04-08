"""智谱 AI 免费模型整合工具库

支持的模型:
- glm-4.7-flash:  文本对话（推荐，200K 上下文）
- glm-4-flash-250414: 文本对话（128K 上下文）
- glm-4.6v-flash: 多模态理解（图片/视频/文件）
- glm-4.1v-thinking-flash: 视觉推理（内置深度思考）
- glm-4v-flash: 图片理解（旧版）
- cogview-3-flash: 图片生成
- cogvideox-flash: 视频生成
"""

from .client import ZhipuFreeClient
from .models import (
    ChatMessage,
    ContentPart,
    ImageUrl,
    VideoUrl,
    FileUrl,
    ThinkingConfig,
    FreeModel,
)

__all__ = [
    "ZhipuFreeClient",
    "ChatMessage",
    "ContentPart",
    "ImageUrl",
    "VideoUrl",
    "FileUrl",
    "ThinkingConfig",
    "FreeModel",
]
