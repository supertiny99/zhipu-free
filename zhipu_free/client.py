"""智谱免费模型统一客户端

零依赖（仅 httpx），整合全部 7 个免费模型 API。
API Key 从参数 > 环境变量 ZHIPU_API_KEY 依次读取。
"""

from __future__ import annotations

import base64
import json
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import httpx

from .config import get_api_key
from .models import (
    ChatMessage,
    ContentPart,
    FileUrl,
    FreeModel,
    ImageUrl,
    ThinkingConfig,
    Tool,
    VideoUrl,
)

BASE_URL = "https://open.bigmodel.cn/api/paas/v4"


class ZhipuFreeClient:
    """智谱免费模型整合客户端"""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = BASE_URL,
        timeout: float = 120,
    ):
        self.api_key = get_api_key(api_key)
        if not self.api_key:
            raise ValueError(
                "缺少 API Key，请通过以下方式之一设置：\n"
                "  1. zhipu config set-key <your-key>\n"
                "  2. export ZHIPU_API_KEY=<your-key>\n"
                "  3. ZhipuFreeClient(api_key=<your-key>)"
            )
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ══════════════════════════════════════════════════════
    #  文本对话 (Chat Completions)
    # ══════════════════════════════════════════════════════

    def chat(
        self,
        messages: list[ChatMessage] | list[dict],
        *,
        model: str | FreeModel = FreeModel.GLM_4_7_FLASH,
        thinking: ThinkingConfig | bool | None = None,
        stream: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: list[Tool] | list[dict] | None = None,
        response_format: dict | None = None,
        **kwargs,
    ) -> dict | Generator[dict, None, None]:
        """通用对话接口，支持所有 Chat 类模型

        Args:
            messages: 消息列表（ChatMessage 或原始 dict）
            model: 模型名称，默认 glm-4.7-flash
            thinking: 思考模式，True 开启 / False 关闭 / ThinkingConfig 精细控制
            stream: 流式输出
            max_tokens: 最大输出 token
            temperature: 采样温度
            tools: Function Call 工具定义
            response_format: 结构化输出格式（如 {"type": "json_object"}）
        """
        payload = self._build_chat_payload(
            messages=messages,
            model=str(model.value if isinstance(model, FreeModel) else model),
            thinking=thinking,
            stream=stream,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
            response_format=response_format,
            **kwargs,
        )
        if stream:
            return self._stream_chat(payload)
        return self._post("/chat/completions", payload)

    # ── 便捷方法：纯文本对话 ───────────────────────────

    def ask(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | FreeModel = FreeModel.GLM_4_7_FLASH,
        thinking: bool = False,
        **kwargs,
    ) -> str:
        """最简文本对话，直接返回回复字符串"""
        msgs: list[ChatMessage] = []
        if system:
            msgs.append(ChatMessage(role="system", content=system))
        msgs.append(ChatMessage(role="user", content=prompt))
        resp = self.chat(msgs, model=model, thinking=thinking, **kwargs)
        return resp["choices"][0]["message"]["content"]

    def ask_stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | FreeModel = FreeModel.GLM_4_7_FLASH,
        thinking: bool = True,
        **kwargs,
    ) -> Generator[str, None, None]:
        """流式文本对话，逐 token 生成"""
        msgs: list[ChatMessage] = []
        if system:
            msgs.append(ChatMessage(role="system", content=system))
        msgs.append(ChatMessage(role="user", content=prompt))
        for chunk in self.chat(msgs, model=model, thinking=thinking, stream=True, **kwargs):
            choices = chunk.get("choices", [])
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            # 先输出推理过程
            if delta.get("reasoning_content"):
                yield delta["reasoning_content"]
            # 再输出最终内容
            if delta.get("content"):
                yield delta["content"]

    # ══════════════════════════════════════════════════════
    #  多模态理解 (Vision)
    # ══════════════════════════════════════════════════════

    def see_image(
        self,
        image: str | Path,
        prompt: str = "描述这张图片",
        *,
        model: str | FreeModel = FreeModel.GLM_4_6V_FLASH,
        thinking: bool = False,
        **kwargs,
    ) -> str:
        """图片理解，支持 URL / 本地文件路径 / Base64"""
        image_url = self._resolve_image(image)
        msgs = [
            ChatMessage(
                role="user",
                content=[
                    ContentPart(image=ImageUrl(url=image_url)),
                    ContentPart(text=prompt),
                ],
            )
        ]
        resp = self.chat(msgs, model=model, thinking=thinking, **kwargs)
        return resp["choices"][0]["message"]["content"]

    def see_video(
        self,
        video_url: str,
        prompt: str = "描述这个视频的内容",
        *,
        model: str | FreeModel = FreeModel.GLM_4_6V_FLASH,
        thinking: bool = False,
        **kwargs,
    ) -> str:
        """视频理解"""
        msgs = [
            ChatMessage(
                role="user",
                content=[
                    ContentPart(video=VideoUrl(url=video_url)),
                    ContentPart(text=prompt),
                ],
            )
        ]
        resp = self.chat(msgs, model=model, thinking=thinking, **kwargs)
        return resp["choices"][0]["message"]["content"]

    def see_file(
        self,
        file_url: str,
        prompt: str = "总结这个文档的内容",
        *,
        model: str | FreeModel = FreeModel.GLM_4_6V_FLASH,
        thinking: bool = False,
        **kwargs,
    ) -> str:
        """文件理解（PDF / TXT 等）"""
        msgs = [
            ChatMessage(
                role="user",
                content=[
                    ContentPart(file=FileUrl(url=file_url)),
                    ContentPart(text=prompt),
                ],
            )
        ]
        resp = self.chat(msgs, model=model, thinking=thinking, **kwargs)
        return resp["choices"][0]["message"]["content"]

    # ══════════════════════════════════════════════════════
    #  图片生成 (CogView)
    # ══════════════════════════════════════════════════════

    def generate_image(
        self,
        prompt: str,
        *,
        model: str | FreeModel = FreeModel.COGVIEW_3_FLASH,
        size: str = "1024x1024",
        **kwargs,
    ) -> str:
        """文本生成图片，返回图片 URL"""
        payload = {
            "model": str(model.value if isinstance(model, FreeModel) else model),
            "prompt": prompt,
            "size": size,
            **kwargs,
        }
        resp = self._post("/images/generations", payload)
        return resp["data"][0]["url"]

    # ══════════════════════════════════════════════════════
    #  视频生成 (CogVideoX) — 异步任务
    # ══════════════════════════════════════════════════════

    def generate_video(
        self,
        prompt: str,
        *,
        model: str | FreeModel = FreeModel.COGVIDEOX_FLASH,
        **kwargs,
    ) -> str:
        """提交视频生成任务，返回 task_id（异步）"""
        payload = {
            "model": str(model.value if isinstance(model, FreeModel) else model),
            "prompt": prompt,
            **kwargs,
        }
        resp = self._post("/videos/generations", payload)
        return resp["id"]

    def get_video_result(self, task_id: str) -> dict:
        """查询视频生成结果

        Returns:
            {"task_status": "SUCCESS"|"PROCESSING"|"FAIL", "video_result": [...]}
        """
        resp = self._client.get(f"/async-result/{task_id}")
        resp.raise_for_status()
        return resp.json()

    # ══════════════════════════════════════════════════════
    #  Function Call 便捷构造
    # ══════════════════════════════════════════════════════

    @staticmethod
    def define_tool(
        name: str,
        description: str,
        parameters: dict,
    ) -> dict:
        """快速构造 Function Call 工具定义

        Example:
            tool = client.define_tool(
                name="get_weather",
                description="查询天气",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名"}
                    },
                    "required": ["city"],
                },
            )
            resp = client.chat(messages, tools=[tool])
        """
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }

    # ══════════════════════════════════════════════════════
    #  内部方法
    # ══════════════════════════════════════════════════════

    def _post(self, path: str, payload: dict) -> dict:
        resp = self._client.post(path, json=payload)
        resp.raise_for_status()
        return resp.json()

    def _stream_chat(self, payload: dict) -> Generator[dict, None, None]:
        with self._client.stream("POST", "/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                yield json.loads(data)

    def _build_chat_payload(
        self,
        *,
        messages: list[ChatMessage] | list[dict],
        model: str,
        thinking: ThinkingConfig | bool | None,
        stream: bool,
        max_tokens: int,
        temperature: float,
        tools: list[Tool] | list[dict] | None,
        response_format: dict | None,
        **kwargs,
    ) -> dict:
        msg_list = []
        for m in messages:
            if isinstance(m, ChatMessage):
                msg_list.append(m.to_dict())
            else:
                msg_list.append(m)

        payload: dict[str, Any] = {
            "model": model,
            "messages": msg_list,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if stream:
            payload["stream"] = True

        # 思考模式
        if thinking is not None:
            if isinstance(thinking, bool):
                thinking = ThinkingConfig(enabled=thinking)
            payload["thinking"] = thinking.to_dict()

        # Function Call
        if tools:
            tool_list = []
            for t in tools:
                if isinstance(t, Tool):
                    tool_list.append(t.to_dict())
                else:
                    tool_list.append(t)
            payload["tools"] = tool_list

        # 结构化输出
        if response_format:
            payload["response_format"] = response_format

        payload.update(kwargs)
        return payload

    @staticmethod
    def _resolve_image(image: str | Path) -> str:
        """将图片路径/URL/Base64 统一为可用的 URL 字符串"""
        if isinstance(image, Path) or (
            isinstance(image, str) and not image.startswith(("http://", "https://", "data:"))
        ):
            path = Path(image)
            if not path.exists():
                raise FileNotFoundError(f"图片文件不存在: {path}")
            suffix = path.suffix.lower().lstrip(".")
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(
                suffix, "png"
            )
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/{mime};base64,{b64}"
        return image
