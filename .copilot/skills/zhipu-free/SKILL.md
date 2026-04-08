---
name: zhipu-free
description: 智谱 AI 免费模型 CLI 工具。用于文本对话、图片理解、视频理解、文件理解、文生图、文生视频。当用户需要调用大模型完成对话、理解图片/视频/文档、生成图片或视频时使用此 skill。
metadata:
  author: supertiny
  version: "0.1.0"
---

# 智谱免费模型 CLI

通过 `zhipu` 命令行工具调用智谱 AI 全部 7 个免费模型。

## 前置条件

- Python >= 3.10，已安装 `zhipu-free` 包
- 环境变量 `ZHIPU_API_KEY` 已设置（从 https://open.bigmodel.cn/ 免费获取）
- 项目路径：`/Users/supertiny/Myproject/xl/bigmodel/free`
- 激活虚拟环境：`source /Users/supertiny/Myproject/xl/bigmodel/free/.venv/bin/activate`

## 命令速查

| 命令 | 用途 | 示例 |
|---|---|---|
| `zhipu ask` | 文本对话 | `zhipu ask "解释量子计算"` |
| `zhipu see` | 图片/视频/文件理解 | `zhipu see photo.jpg "图里有什么"` |
| `zhipu image` | 文生图 | `zhipu image "赛博朋克城市"` |
| `zhipu video` | 文生视频（异步） | `zhipu video "日落海滩"` |
| `zhipu models` | 列出所有免费模型 | `zhipu models` |
| `zhipu web` | 启动 Web UI | `zhipu web --port 7860` |

## 详细用法

### 文本对话

```bash
# 基本对话
zhipu ask "你好，介绍一下自己"

# 带系统提示词
zhipu ask "写一首关于春天的诗" -s "你是一位唐代诗人"

# 启用深度思考（适合复杂推理任务）
zhipu ask "证明根号2是无理数" --think

# 指定模型
zhipu ask "hello" -m glm-4-flash-250414

# 非流式输出（一次返回完整结果）
zhipu ask "简短回答：1+1=?" --no-stream

# 调整参数
zhipu ask "写一个故事" --max-tokens 8192 --temperature 0.9
```

### 图片理解

```bash
# 本地图片
zhipu see /path/to/photo.jpg "描述这张图片"

# URL 图片
zhipu see "https://example.com/image.jpg" "这张图里有什么动物"

# 启用深度思考
zhipu see diagram.png "分析这个架构图" --think

# 指定模型
zhipu see photo.jpg -m glm-4.1v-thinking-flash
```

### 视频理解

```bash
zhipu see "https://example.com/video.mp4" "总结视频内容" --type video
```

### 文件理解

```bash
zhipu see "https://example.com/doc.pdf" "总结文档要点" --type file
```

### 文生图

```bash
# 默认 1024x1024
zhipu image "一只穿太空服的柴犬在月球行走"

# 指定尺寸
zhipu image "山水画" --size 1344x768
```

**可用尺寸**: `1024x1024`, `768x1344`, `864x1152`, `1344x768`, `1152x864`, `1440x720`, `720x1440`

### 文生视频（异步）

```bash
# 提交任务，返回 task_id
zhipu video "一只金毛在沙滩上奔跑"
# 输出: 视频任务已提交: <task_id>
```

视频生成是异步任务，提交后返回 task_id，需要轮询查询结果。

## 可用模型

| 模型 | 类型 | 特点 |
|---|---|---|
| `glm-4.7-flash` | 文本对话（推荐） | 200K 上下文，思考/Function Call/结构化输出 |
| `glm-4-flash-250414` | 文本对话 | 128K 上下文，Function Call/结构化输出 |
| `glm-4.6v-flash` | 多模态（推荐） | 图片/视频/文件理解，思考/Function Call |
| `glm-4.1v-thinking-flash` | 视觉推理 | 内置深度思考 |
| `glm-4v-flash` | 图片理解 | 基础图片理解（旧版） |
| `cogview-3-flash` | 图片生成 | 多分辨率文生图 |
| `cogvideox-flash` | 视频生成 | 文生视频（异步任务） |

## Python API 用法

当 CLI 不够灵活时，可直接调用 Python API：

```python
from zhipu_free import ZhipuFreeClient

client = ZhipuFreeClient()

# 文本对话
answer = client.ask("你好")

# 流式对话
for token in client.ask_stream("写一首诗", thinking=True):
    print(token, end="")

# 图片理解
desc = client.see_image("photo.jpg", "描述这张图片")

# 文生图
url = client.generate_image("赛博朋克城市", size="1024x1024")

# 文生视频
task_id = client.generate_video("日落海滩")
result = client.get_video_result(task_id)

client.close()
```

## Agent 使用指南

1. **对话任务** → `zhipu ask`，复杂推理加 `--think`
2. **分析图片** → `zhipu see <path>`，本地文件直接传路径
3. **生成图片** → `zhipu image`，返回图片 URL
4. **生成视频** → `zhipu video`，异步任务需等待
5. 所有命令输出到 stdout，可管道组合
6. 出错时检查 `ZHIPU_API_KEY` 环境变量是否已设置
