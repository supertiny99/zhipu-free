"""ZhipuFreeClient 单元测试（mock HTTP 请求）"""

import json
from unittest.mock import MagicMock, patch

import pytest

from zhipu_free import ChatMessage, FreeModel, ZhipuFreeClient
from zhipu_free.models import ContentPart, ImageUrl, ThinkingConfig


# ── fixtures ─────────────────────────────────────────────


@pytest.fixture
def client():
    return ZhipuFreeClient(api_key="test-key-123")


def _mock_chat_response(content: str = "你好") -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                }
            }
        ]
    }


# ── 初始化测试 ───────────────────────────────────────────


def test_missing_api_key():
    """缺少 API Key 应抛出 ValueError"""
    import os
    old = os.environ.pop("ZHIPU_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="缺少 API Key"):
            ZhipuFreeClient()
    finally:
        if old:
            os.environ["ZHIPU_API_KEY"] = old


def test_env_api_key():
    """从环境变量读取 API Key"""
    import os
    os.environ["ZHIPU_API_KEY"] = "env-test-key"
    try:
        c = ZhipuFreeClient()
        assert c.api_key == "env-test-key"
        c.close()
    finally:
        del os.environ["ZHIPU_API_KEY"]


# ── 模型枚举测试 ─────────────────────────────────────────


def test_free_model_values():
    """确认所有免费模型枚举值正确"""
    assert FreeModel.GLM_4_7_FLASH.value == "glm-4.7-flash"
    assert FreeModel.GLM_4_FLASH.value == "glm-4-flash-250414"
    assert FreeModel.GLM_4_6V_FLASH.value == "glm-4.6v-flash"
    assert FreeModel.GLM_4_1V_THINKING.value == "glm-4.1v-thinking-flash"
    assert FreeModel.GLM_4V_FLASH.value == "glm-4v-flash"
    assert FreeModel.COGVIEW_3_FLASH.value == "cogview-3-flash"
    assert FreeModel.COGVIDEOX_FLASH.value == "cogvideox-flash"


# ── 消息构造测试 ─────────────────────────────────────────


def test_chat_message_text():
    msg = ChatMessage(role="user", content="hello")
    assert msg.to_dict() == {"role": "user", "content": "hello"}


def test_chat_message_multimodal():
    msg = ChatMessage(
        role="user",
        content=[
            ContentPart(image=ImageUrl(url="https://example.com/img.png")),
            ContentPart(text="描述这张图片"),
        ],
    )
    d = msg.to_dict()
    assert d["role"] == "user"
    assert len(d["content"]) == 2
    assert d["content"][0]["type"] == "image_url"
    assert d["content"][1]["type"] == "text"


def test_thinking_config():
    assert ThinkingConfig(enabled=True).to_dict() == {"type": "enabled"}
    assert ThinkingConfig(enabled=False).to_dict() == {"type": "disabled"}
    assert ThinkingConfig(enabled=True, budget_tokens=1024).to_dict() == {
        "type": "enabled",
        "budget_tokens": 1024,
    }


# ── ask() 测试 ───────────────────────────────────────────


@patch.object(ZhipuFreeClient, "_post")
def test_ask(mock_post, client):
    mock_post.return_value = _mock_chat_response("量子力学核心原理")
    result = client.ask("量子计算是什么？")
    assert result == "量子力学核心原理"

    # 验证 payload 结构
    call_args = mock_post.call_args
    payload = call_args[0][1]
    assert payload["model"] == "glm-4.7-flash"
    assert len(payload["messages"]) == 1
    assert payload["messages"][0]["role"] == "user"


@patch.object(ZhipuFreeClient, "_post")
def test_ask_with_system(mock_post, client):
    mock_post.return_value = _mock_chat_response("优化建议")
    result = client.ask("如何优化？", system="你是专家")
    assert result == "优化建议"

    payload = mock_post.call_args[0][1]
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["role"] == "system"


@patch.object(ZhipuFreeClient, "_post")
def test_ask_with_model(mock_post, client):
    mock_post.return_value = _mock_chat_response("hi")
    client.ask("hello", model=FreeModel.GLM_4_FLASH)
    payload = mock_post.call_args[0][1]
    assert payload["model"] == "glm-4-flash-250414"


# ── chat() payload 构建测试 ──────────────────────────────


@patch.object(ZhipuFreeClient, "_post")
def test_chat_with_thinking(mock_post, client):
    mock_post.return_value = _mock_chat_response("思考结果")
    client.chat(
        [ChatMessage(role="user", content="test")],
        thinking=True,
        max_tokens=65536,
        temperature=1.0,
    )
    payload = mock_post.call_args[0][1]
    assert payload["thinking"] == {"type": "enabled"}
    assert payload["max_tokens"] == 65536
    assert payload["temperature"] == 1.0


@patch.object(ZhipuFreeClient, "_post")
def test_chat_with_tools(mock_post, client):
    mock_post.return_value = _mock_chat_response("tool response")
    tool = client.define_tool(
        "get_weather",
        "查询天气",
        {"type": "object", "properties": {"city": {"type": "string"}}},
    )
    client.chat(
        [ChatMessage(role="user", content="北京天气")],
        tools=[tool],
    )
    payload = mock_post.call_args[0][1]
    assert len(payload["tools"]) == 1
    assert payload["tools"][0]["function"]["name"] == "get_weather"


@patch.object(ZhipuFreeClient, "_post")
def test_chat_with_response_format(mock_post, client):
    mock_post.return_value = _mock_chat_response('{"items": []}')
    client.chat(
        [ChatMessage(role="user", content="列表")],
        response_format={"type": "json_object"},
    )
    payload = mock_post.call_args[0][1]
    assert payload["response_format"] == {"type": "json_object"}


# ── 多模态便捷方法测试 ───────────────────────────────────


@patch.object(ZhipuFreeClient, "_post")
def test_see_image(mock_post, client):
    mock_post.return_value = _mock_chat_response("一只猫")
    result = client.see_image("https://example.com/cat.jpg", "图里有什么？")
    assert result == "一只猫"
    payload = mock_post.call_args[0][1]
    assert payload["model"] == "glm-4.6v-flash"
    content = payload["messages"][0]["content"]
    assert content[0]["type"] == "image_url"
    assert content[1]["type"] == "text"


@patch.object(ZhipuFreeClient, "_post")
def test_see_video(mock_post, client):
    mock_post.return_value = _mock_chat_response("视频内容")
    result = client.see_video("https://example.com/v.mov")
    assert result == "视频内容"
    payload = mock_post.call_args[0][1]
    content = payload["messages"][0]["content"]
    assert content[0]["type"] == "video_url"


@patch.object(ZhipuFreeClient, "_post")
def test_see_file(mock_post, client):
    mock_post.return_value = _mock_chat_response("文档摘要")
    result = client.see_file("https://example.com/doc.pdf")
    assert result == "文档摘要"
    payload = mock_post.call_args[0][1]
    content = payload["messages"][0]["content"]
    assert content[0]["type"] == "file_url"


# ── 图片生成测试 ─────────────────────────────────────────


@patch.object(ZhipuFreeClient, "_post")
def test_generate_image(mock_post, client):
    mock_post.return_value = {"data": [{"url": "https://cdn.example.com/img.png"}]}
    url = client.generate_image("一只猫", size="768x1344")
    assert url == "https://cdn.example.com/img.png"
    payload = mock_post.call_args[0][1]
    assert payload["model"] == "cogview-3-flash"
    assert payload["size"] == "768x1344"


# ── 视频生成测试 ─────────────────────────────────────────


@patch.object(ZhipuFreeClient, "_post")
def test_generate_video(mock_post, client):
    mock_post.return_value = {"id": "task-abc-123"}
    task_id = client.generate_video("一只猫弹钢琴")
    assert task_id == "task-abc-123"
    payload = mock_post.call_args[0][1]
    assert payload["model"] == "cogvideox-flash"


# ── 图片路径解析测试 ─────────────────────────────────────


def test_resolve_image_url(client):
    assert client._resolve_image("https://example.com/a.png") == "https://example.com/a.png"


def test_resolve_image_file_not_found(client):
    with pytest.raises(FileNotFoundError):
        client._resolve_image("/nonexistent/path.png")


def test_resolve_image_local_file(client, tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    result = client._resolve_image(str(img))
    assert result.startswith("data:image/png;base64,")


# ── define_tool 测试 ─────────────────────────────────────


def test_define_tool():
    tool = ZhipuFreeClient.define_tool(
        "search", "搜索", {"type": "object", "properties": {}}
    )
    assert tool["type"] == "function"
    assert tool["function"]["name"] == "search"
    assert tool["function"]["description"] == "搜索"


# ── context manager 测试 ─────────────────────────────────


def test_context_manager():
    with ZhipuFreeClient(api_key="test-key") as c:
        assert c.api_key == "test-key"
