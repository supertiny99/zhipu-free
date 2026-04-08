"""智谱免费模型 CLI 工具

用法:
    zhipu ask "你好"
    zhipu ask "解释量子计算" --think
    zhipu ask "写一首诗" --model glm-4-flash-250414
    zhipu image "赛博朋克城市" --size 1024x1024
    zhipu see photo.jpg "图里有什么？"
    zhipu models
"""

from __future__ import annotations

import argparse
import os
import sys

from .client import ZhipuFreeClient
from .models import FreeModel


def main():
    parser = argparse.ArgumentParser(
        prog="zhipu",
        description="智谱 AI 免费模型命令行工具",
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    # ── ask ──────────────────────────────────────────
    p_ask = sub.add_parser("ask", help="文本对话")
    p_ask.add_argument("prompt", help="提问内容")
    p_ask.add_argument("-s", "--system", help="系统提示词")
    p_ask.add_argument("-m", "--model", default="glm-4.7-flash", help="模型名称")
    p_ask.add_argument("--think", action="store_true", help="启用深度思考")
    p_ask.add_argument("--no-stream", action="store_true", help="禁用流式输出")
    p_ask.add_argument("--max-tokens", type=int, default=4096)
    p_ask.add_argument("--temperature", type=float, default=0.7)

    # ── see ──────────────────────────────────────────
    p_see = sub.add_parser("see", help="图片/视频/文件理解")
    p_see.add_argument("file", help="图片/视频/文件 URL 或本地路径")
    p_see.add_argument("prompt", nargs="?", default="描述这个内容", help="提问内容")
    p_see.add_argument("-m", "--model", default="glm-4.6v-flash")
    p_see.add_argument("--think", action="store_true")
    p_see.add_argument("--type", choices=["image", "video", "file"], default="image", help="内容类型")

    # ── image ────────────────────────────────────────
    p_img = sub.add_parser("image", help="文生图")
    p_img.add_argument("prompt", help="图片描述")
    p_img.add_argument("--size", default="1024x1024", help="图片尺寸")

    # ── video ────────────────────────────────────────
    p_vid = sub.add_parser("video", help="文生视频（异步）")
    p_vid.add_argument("prompt", help="视频描述")

    # ── config ────────────────────────────────────────
    p_cfg = sub.add_parser("config", help="管理配置（API Key 等）")
    cfg_sub = p_cfg.add_subparsers(dest="config_action")
    cfg_set = cfg_sub.add_parser("set-key", help="保存 API Key")
    cfg_set.add_argument("key", help="API Key")
    cfg_sub.add_parser("show", help="显示当前配置")
    cfg_sub.add_parser("clear-key", help="清除已保存的 API Key")

    # ── models ───────────────────────────────────────
    sub.add_parser("models", help="列出所有免费模型")

    # ── web ──────────────────────────────────────────
    p_web = sub.add_parser("web", help="启动 Web UI（需要 gradio）")
    p_web.add_argument("--port", type=int, default=7860, help="端口")
    p_web.add_argument("--share", action="store_true", help="生成公共链接")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "models":
        _cmd_models()
        return

    if args.command == "config":
        _cmd_config(args)
        return

    if args.command == "web":
        _cmd_web(args)
        return

    client = ZhipuFreeClient()

    try:
        if args.command == "ask":
            _cmd_ask(client, args)
        elif args.command == "see":
            _cmd_see(client, args)
        elif args.command == "image":
            _cmd_image(client, args)
        elif args.command == "video":
            _cmd_video(client, args)
    finally:
        client.close()


def _cmd_ask(client: ZhipuFreeClient, args):
    if args.no_stream:
        result = client.ask(
            args.prompt,
            system=args.system,
            model=args.model,
            thinking=args.think,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        print(result)
    else:
        for token in client.ask_stream(
            args.prompt,
            system=args.system,
            model=args.model,
            thinking=args.think,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        ):
            print(token, end="", flush=True)
        print()


def _cmd_see(client: ZhipuFreeClient, args):
    if args.type == "video":
        result = client.see_video(args.file, args.prompt, model=args.model, thinking=args.think)
    elif args.type == "file":
        result = client.see_file(args.file, args.prompt, model=args.model, thinking=args.think)
    else:
        result = client.see_image(args.file, args.prompt, model=args.model, thinking=args.think)
    print(result)


def _cmd_image(client: ZhipuFreeClient, args):
    url = client.generate_image(args.prompt, size=args.size)
    print(f"图片已生成: {url}")


def _cmd_video(client: ZhipuFreeClient, args):
    task_id = client.generate_video(args.prompt)
    print(f"视频任务已提交: {task_id}")
    print(f"查询结果: zhipu video-status {task_id}")


def _cmd_models():
    print("智谱免费模型列表:\n")
    models = [
        ("glm-4.7-flash", "文本对话", "200K 上下文，支持思考/Function Call/结构化输出"),
        ("glm-4-flash-250414", "文本对话", "128K 上下文，支持 Function Call/结构化输出"),
        ("glm-4.6v-flash", "多模态", "图片/视频/文件理解，支持思考/Function Call"),
        ("glm-4.1v-thinking-flash", "视觉推理", "内置深度思考，图片/视频/文件理解"),
        ("glm-4v-flash", "图片理解", "基础图片理解（旧版）"),
        ("cogview-3-flash", "图片生成", "文本→图片，多分辨率"),
        ("cogvideox-flash", "视频生成", "文本→视频（异步）"),
    ]
    for name, category, desc in models:
        print(f"  {name:<30} [{category}] {desc}")


def _cmd_web(args):
    try:
        from .web import create_app
    except ImportError:
        print("需要安装 gradio: pip install gradio>=5")
        sys.exit(1)
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=args.port, share=args.share)


def _cmd_config(args):
    from .config import clear_api_key, get_api_key, get_config, set_api_key, CONFIG_FILE

    if args.config_action == "set-key":
        set_api_key(args.key)
        print(f"API Key 已保存到 {CONFIG_FILE}")
    elif args.config_action == "show":
        config = get_config()
        key = get_api_key()
        source = "未找到"
        if key:
            if config.get("api_key") == key:
                source = f"配置文件 ({CONFIG_FILE})"
            elif os.environ.get("ZHIPU_API_KEY") == key:
                source = "环境变量 ZHIPU_API_KEY"
            else:
                source = "函数参数"
            masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
            print(f"API Key: {masked}")
            print(f"来源:    {source}")
        else:
            print("未配置 API Key")
            print(f"\n设置方法:")
            print(f"  zhipu config set-key <your-key>")
            print(f"  export ZHIPU_API_KEY=<your-key>")
    elif args.config_action == "clear-key":
        clear_api_key()
        print("已清除配置文件中的 API Key")
    else:
        print("用法:")
        print("  zhipu config set-key <key>   保存 API Key")
        print("  zhipu config show            显示配置")
        print("  zhipu config clear-key       清除 API Key")


if __name__ == "__main__":
    main()
