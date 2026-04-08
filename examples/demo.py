"""使用示例

运行前设置环境变量: export ZHIPU_API_KEY="your-api-key"
"""

from zhipu_free import ZhipuFreeClient, FreeModel

client = ZhipuFreeClient()


# ═══════════════════════════════════════════════════════
#  1. 最简对话 — ask()
# ═══════════════════════════════════════════════════════

print("=== 简单问答 ===")
answer = client.ask("量子计算的核心原理是什么？用三句话概括")
print(answer)


# ═══════════════════════════════════════════════════════
#  2. 带 system prompt 的对话
# ═══════════════════════════════════════════════════════

print("\n=== 角色扮演 ===")
answer = client.ask(
    "如何快速提升 Python 性能？",
    system="你是一位资深 Python 性能优化专家，回答简洁精准",
)
print(answer)


# ═══════════════════════════════════════════════════════
#  3. 深度思考模式 + 流式输出
# ═══════════════════════════════════════════════════════

print("\n=== 流式 + 深度思考 ===")
for token in client.ask_stream("证明 √2 是无理数", thinking=True):
    print(token, end="", flush=True)
print()


# ═══════════════════════════════════════════════════════
#  4. 图片理解
# ═══════════════════════════════════════════════════════

print("\n=== 图片理解 ===")
desc = client.see_image(
    "https://cdn.bigmodel.cn/static/logo/register.png",
    "这张图片里有什么内容？",
)
print(desc)


# ═══════════════════════════════════════════════════════
#  5. 本地图片理解（自动 Base64 编码）
# ═══════════════════════════════════════════════════════

# desc = client.see_image("./my_photo.jpg", "描述图片内容")


# ═══════════════════════════════════════════════════════
#  6. 视频理解
# ═══════════════════════════════════════════════════════

print("\n=== 视频理解 ===")
summary = client.see_video(
    "https://cdn.bigmodel.cn/agent-demos/lark/113123.mov",
    "这个视频讲了什么？",
)
print(summary)


# ═══════════════════════════════════════════════════════
#  7. 文件理解
# ═══════════════════════════════════════════════════════

print("\n=== 文件理解 ===")
digest = client.see_file(
    "https://cdn.bigmodel.cn/static/demo/demo1.pdf",
    "总结这个文档的要点",
)
print(digest)


# ═══════════════════════════════════════════════════════
#  8. 图片生成
# ═══════════════════════════════════════════════════════

print("\n=== 图片生成 ===")
url = client.generate_image(
    "一只穿着太空服的柴犬，在月球表面行走，背景是地球",
    size="1024x1024",
)
print(f"生成图片: {url}")


# ═══════════════════════════════════════════════════════
#  9. 视频生成（异步任务）
# ═══════════════════════════════════════════════════════

print("\n=== 视频生成 ===")
task_id = client.generate_video("一只猫咪在钢琴上弹奏月光奏鸣曲")
print(f"任务已提交: {task_id}")

# 轮询结果
import time
for _ in range(60):
    result = client.get_video_result(task_id)
    status = result.get("task_status")
    print(f"  状态: {status}")
    if status == "SUCCESS":
        print(f"  视频: {result['video_result']}")
        break
    if status == "FAIL":
        print(f"  失败: {result}")
        break
    time.sleep(5)


# ═══════════════════════════════════════════════════════
#  10. Function Call（工具调用）
# ═══════════════════════════════════════════════════════

print("\n=== Function Call ===")
weather_tool = client.define_tool(
    name="get_weather",
    description="查询指定城市的天气",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"},
        },
        "required": ["city"],
    },
)

from zhipu_free import ChatMessage

resp = client.chat(
    messages=[ChatMessage(role="user", content="北京今天天气怎么样？")],
    tools=[weather_tool],
)
print(resp["choices"][0]["message"])


# ═══════════════════════════════════════════════════════
#  11. 结构化 JSON 输出
# ═══════════════════════════════════════════════════════

print("\n=== 结构化输出 ===")
resp = client.chat(
    messages=[
        ChatMessage(
            role="user",
            content="列出 3 个 Python Web 框架，包含名称和简介",
        )
    ],
    response_format={"type": "json_object"},
)
print(resp["choices"][0]["message"]["content"])


# ═══════════════════════════════════════════════════════
#  12. 使用旧版模型
# ═══════════════════════════════════════════════════════

print("\n=== 使用 GLM-4-Flash（旧版）===")
answer = client.ask(
    "你好，介绍一下你自己",
    model=FreeModel.GLM_4_FLASH,
)
print(answer)

client.close()
