"""智谱免费模型 Web UI（Gradio）

启动方式:
    python -m zhipu_free.web
    # 或
    ZHIPU_API_KEY=xxx python zhipu_free/web.py
"""

from __future__ import annotations

import os
import time

import gradio as gr

from .client import ZhipuFreeClient
from .models import FreeModel

# ── 模型选项 ─────────────────────────────────────────────

CHAT_MODELS = [
    ("GLM-4.7-Flash（推荐）", "glm-4.7-flash"),
    ("GLM-4-Flash-250414", "glm-4-flash-250414"),
]

VISION_MODELS = [
    ("GLM-4.6V-Flash（推荐）", "glm-4.6v-flash"),
    ("GLM-4.1V-Thinking-Flash", "glm-4.1v-thinking-flash"),
    ("GLM-4V-Flash（旧版）", "glm-4v-flash"),
]

IMAGE_SIZES = [
    "1024x1024",
    "768x1344",
    "864x1152",
    "1344x768",
    "1152x864",
    "1440x720",
    "720x1440",
]


def _get_client() -> ZhipuFreeClient:
    return ZhipuFreeClient()


# ── 对话 Tab ─────────────────────────────────────────────


def chat_respond(message, history, model, thinking, system_prompt):
    client = _get_client()
    try:
        from .models import ChatMessage

        msgs = []
        if system_prompt:
            msgs.append(ChatMessage(role="system", content=system_prompt))
        for h in history:
            msgs.append(ChatMessage(role="user", content=h["content"] if h["role"] == "user" else ""))
            if h["role"] == "assistant":
                msgs.append(ChatMessage(role="assistant", content=h["content"]))
        # 重建：正确映射 history
        msgs = []
        if system_prompt:
            msgs.append(ChatMessage(role="system", content=system_prompt))
        for h in history:
            msgs.append(ChatMessage(role=h["role"], content=h["content"]))
        msgs.append(ChatMessage(role="user", content=message))

        partial = ""
        for token in client.ask_stream(
            message,
            system=system_prompt if system_prompt else None,
            model=model,
            thinking=thinking,
        ):
            partial += token
            yield partial
    finally:
        client.close()


# ── 图片理解 Tab ─────────────────────────────────────────


def see_image_fn(image_path, prompt, model, thinking):
    if not image_path:
        return "请先上传一张图片"
    client = _get_client()
    try:
        return client.see_image(
            image_path,
            prompt or "描述这张图片",
            model=model,
            thinking=thinking,
        )
    finally:
        client.close()


# ── 图片生成 Tab ─────────────────────────────────────────


def gen_image_fn(prompt, size):
    if not prompt:
        return None, "请输入图片描述"
    client = _get_client()
    try:
        url = client.generate_image(prompt, size=size)
        return url, f"生成成功: {url}"
    except Exception as e:
        return None, f"生成失败: {e}"
    finally:
        client.close()


# ── 视频生成 Tab ─────────────────────────────────────────


def gen_video_fn(prompt, progress=gr.Progress()):
    """提交视频生成任务并轮询结果"""
    if not prompt:
        yield "请输入视频描述", None
        return
    client = _get_client()
    try:
        progress(0, desc="提交任务...")
        task_id = client.generate_video(prompt)
        yield f"任务已提交，ID: {task_id}\n等待生成中...", None

        for i in range(120):  # 最多轮询 10 分钟
            time.sleep(5)
            result = client.get_video_result(task_id)
            status = result.get("task_status", "UNKNOWN")
            progress((i + 1) / 120, desc=f"状态: {status}")

            if status == "SUCCESS":
                video_list = result.get("video_result", [])
                if video_list:
                    video_url = video_list[0].get("url", "")
                    yield f"生成成功！\n视频链接: {video_url}", video_url
                    return
                yield "生成完成但未返回视频链接", None
                return
            elif status == "FAIL":
                yield f"生成失败: {result}", None
                return
            else:
                yield f"任务 {task_id}\n状态: {status}（已等待 {(i+1)*5} 秒）", None

        yield f"任务 {task_id} 超时，请稍后用 task_id 手动查询", None
    except Exception as e:
        yield f"出错: {e}", None
    finally:
        client.close()


# ── 构建界面 ─────────────────────────────────────────────


def create_app() -> gr.Blocks:
    with gr.Blocks(title="智谱免费模型") as app:
        gr.Markdown("# 🤖 智谱 AI 免费模型工具箱\n全部 7 个免费模型，一站体验")

        with gr.Tabs():
            # ── Tab 1: 对话 ──
            with gr.Tab("💬 对话"):
                with gr.Row():
                    with gr.Column(scale=1):
                        chat_model = gr.Dropdown(
                            choices=CHAT_MODELS,
                            value="glm-4.7-flash",
                            label="模型",
                        )
                        chat_thinking = gr.Checkbox(label="深度思考", value=False)
                        chat_system = gr.Textbox(
                            label="系统提示词（可选）",
                            placeholder="你是一位...",
                            lines=3,
                        )
                with gr.Row():
                    chatbot = gr.ChatInterface(
                        fn=chat_respond,
                        additional_inputs=[chat_model, chat_thinking, chat_system],
                    )

            # ── Tab 2: 图片理解 ──
            with gr.Tab("👁️ 图片理解"):
                with gr.Row():
                    with gr.Column():
                        img_input = gr.Image(type="filepath", label="上传图片")
                        img_prompt = gr.Textbox(
                            label="提问",
                            value="描述这张图片的内容",
                            placeholder="你想了解什么？",
                        )
                        with gr.Row():
                            img_model = gr.Dropdown(
                                choices=VISION_MODELS,
                                value="glm-4.6v-flash",
                                label="模型",
                            )
                            img_thinking = gr.Checkbox(label="深度思考")
                        img_btn = gr.Button("🔍 分析", variant="primary")
                    with gr.Column():
                        img_output = gr.Textbox(label="分析结果", lines=15)

                img_btn.click(
                    see_image_fn,
                    inputs=[img_input, img_prompt, img_model, img_thinking],
                    outputs=img_output,
                )

            # ── Tab 3: 图片生成 ──
            with gr.Tab("🎨 图片生成"):
                with gr.Row():
                    with gr.Column():
                        gen_prompt = gr.Textbox(
                            label="图片描述",
                            placeholder="一只穿太空服的柴犬在月球行走",
                            lines=3,
                        )
                        gen_size = gr.Dropdown(
                            choices=IMAGE_SIZES,
                            value="1024x1024",
                            label="尺寸",
                        )
                        gen_btn = gr.Button("🖼️ 生成", variant="primary")
                        gen_status = gr.Textbox(label="状态")
                    with gr.Column():
                        gen_output = gr.Image(label="生成结果")

                gen_btn.click(
                    gen_image_fn,
                    inputs=[gen_prompt, gen_size],
                    outputs=[gen_output, gen_status],
                )

            # ── Tab 4: 视频生成 ──
            with gr.Tab("🎬 视频生成"):
                with gr.Row():
                    with gr.Column():
                        vid_prompt = gr.Textbox(
                            label="视频描述",
                            placeholder="一只金毛在沙滩上奔跑，阳光洒在海面上",
                            lines=3,
                        )
                        vid_btn = gr.Button("🎬 生成视频", variant="primary")
                        vid_status = gr.Textbox(label="状态", lines=5)
                    with gr.Column():
                        vid_output = gr.Video(label="生成结果")

                vid_btn.click(
                    gen_video_fn,
                    inputs=[vid_prompt],
                    outputs=[vid_status, vid_output],
                )

            # ── Tab 5: 模型列表 ──
            with gr.Tab("📋 模型列表"):
                gr.Markdown("""
| 模型 | 类型 | 能力 |
|---|---|---|
| `glm-4.7-flash` | 文本对话 | 200K 上下文，思考/Function Call/结构化输出 |
| `glm-4-flash-250414` | 文本对话 | 128K 上下文，Function Call/结构化输出 |
| `glm-4.6v-flash` | 多模态 | 图片/视频/文件理解，思考/Function Call |
| `glm-4.1v-thinking-flash` | 视觉推理 | 内置深度思考 |
| `glm-4v-flash` | 图片理解 | 基础图片理解 |
| `cogview-3-flash` | 图片生成 | 多分辨率 |
| `cogvideox-flash` | 视频生成 | 异步任务 |

**API Key**: 从 [智谱开放平台](https://open.bigmodel.cn/) 免费注册获取

**环境变量**: `export ZHIPU_API_KEY="your-key"`
                """)

    return app


def main():
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False, theme=gr.themes.Soft())


if __name__ == "__main__":
    main()
