# 智谱 AI 免费模型工具箱

整合智谱全部 7 个免费模型 API，提供 Python 库、CLI 命令行、Web UI 三种使用方式。

## 支持的免费模型

| 模型 | 类型 | 能力 |
|---|---|---|
| `glm-4.7-flash` | 文本对话 | 200K 上下文，思考模式 / Function Call / 结构化输出 |
| `glm-4-flash-250414` | 文本对话 | 128K 上下文，Function Call / 结构化输出 |
| `glm-4.6v-flash` | 多模态理解 | 图片 / 视频 / 文件理解，思考模式 / Function Call |
| `glm-4.1v-thinking-flash` | 视觉推理 | 内置深度思考，图片 / 视频 / 文件理解 |
| `glm-4v-flash` | 图片理解 | 基础图片理解 |
| `cogview-3-flash` | 图片生成 | 文本 → 图片，多分辨率 |
| `cogvideox-flash` | 视频生成 | 文本 → 视频（异步任务） |

## 快速开始

### 1. 获取 API Key

前往 [智谱开放平台](https://open.bigmodel.cn/) 注册，免费获取 API Key。

### 2. 安装

```bash
# 从 GitHub 安装
pip install git+https://github.com/supertiny/zhipu-free.git

# 带 Web UI
pip install "zhipu-free[web] @ git+https://github.com/supertiny/zhipu-free.git"
```

### 3. 设置 API Key

```bash
export ZHIPU_API_KEY="your-api-key"
```

---

## 使用方式一：Python 库

```python
from zhipu_free import ZhipuFreeClient, FreeModel

client = ZhipuFreeClient()
```

### 文本对话

```python
# 最简问答
answer = client.ask("量子计算是什么？")

# 带系统提示词
answer = client.ask(
    "如何优化 SQL 查询？",
    system="你是一位资深 DBA",
)

# 深度思考 + 流式输出
for token in client.ask_stream("证明 √2 是无理数", thinking=True):
    print(token, end="", flush=True)
```

### 图片理解

```python
# URL 图片
desc = client.see_image("https://example.com/photo.jpg", "图里有什么？")

# 本地图片（自动 Base64 编码）
desc = client.see_image("./my_photo.jpg", "描述内容")
```

### 视频理解

```python
summary = client.see_video("https://example.com/video.mov", "总结视频内容")
```

### 文件理解

```python
digest = client.see_file("https://example.com/doc.pdf", "总结要点")
```

### 图片生成

```python
url = client.generate_image("赛博朋克风格的未来城市", size="1024x1024")
```

### 视频生成（异步）

```python
task_id = client.generate_video("一只猫咪弹钢琴")

# 轮询结果
import time
for _ in range(60):
    result = client.get_video_result(task_id)
    if result["task_status"] == "SUCCESS":
        print(result["video_result"])
        break
    time.sleep(5)
```

### Function Call（工具调用）

```python
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

from zhipu_free import ChatMessage
resp = client.chat(
    [ChatMessage(role="user", content="北京天气如何？")],
    tools=[tool],
)
```

### 结构化 JSON 输出

```python
resp = client.chat(
    [ChatMessage(role="user", content="列出3个Python Web框架")],
    response_format={"type": "json_object"},
)
```

### 切换模型

```python
# 使用旧版模型
answer = client.ask("你好", model=FreeModel.GLM_4_FLASH)

# 使用视觉推理模型
desc = client.see_image("photo.jpg", "分析图片", model=FreeModel.GLM_4_1V_THINKING)
```

---

## 使用方式二：CLI 命令行

```bash
# 文本对话
python -m zhipu_free ask "量子计算是什么？"

# 深度思考模式
python -m zhipu_free ask "证明勾股定理" --think

# 指定模型
python -m zhipu_free ask "你好" --model glm-4-flash-250414

# 带系统提示词
python -m zhipu_free ask "优化建议" --system "你是DBA专家"

# 非流式输出
python -m zhipu_free ask "你好" --no-stream

# 图片理解
python -m zhipu_free see photo.jpg "图里有什么？"

# 视频理解
python -m zhipu_free see video.mov "总结内容" --type video

# 文件理解
python -m zhipu_free see doc.pdf "总结要点" --type file

# 图片生成
python -m zhipu_free image "赛博朋克城市" --size 1024x1024

# 视频生成
python -m zhipu_free video "猫咪弹钢琴"

# 查看所有免费模型
python -m zhipu_free models
```

---

## 使用方式三：Web UI

面向普通用户，浏览器打开即可使用。

### 启动

```bash
# 安装 gradio（首次）
pip install gradio

# 启动 Web UI
python -m zhipu_free web
```

启动后访问 **http://localhost:7860**

### 功能

Web UI 提供 4 个页面：

| 页面 | 功能 |
|---|---|
| 💬 对话 | 多轮文本对话，可选模型和深度思考 |
| 👁️ 图片理解 | 上传图片，AI 分析内容 |
| 🎨 图片生成 | 输入描述，生成图片 |
| 🎬 视频生成 | 输入描述，异步生成视频 |
| 📋 模型列表 | 查看所有免费模型信息 |

### 自定义端口

```bash
python -m zhipu_free web --port 8080
```

### 公共访问

生成临时公共链接（通过 Gradio 代理），分享给他人：

```bash
python -m zhipu_free web --share
```

---

## 项目结构

```
.
├── zhipu_free/
│   ├── __init__.py       # 导出入口
│   ├── __main__.py       # python -m 支持
│   ├── models.py         # 数据模型、FreeModel 枚举
│   ├── client.py         # 统一客户端 ZhipuFreeClient
│   ├── cli.py            # CLI 命令行工具
│   └── web.py            # Gradio Web UI
├── .copilot/
│   └── skills/zhipu-free/SKILL.md  # AI Agent Skill 文件
├── tests/
│   └── test_client.py    # 单元测试（22个）
├── examples/
│   └── demo.py           # 完整使用示例
├── pages/
│   └── free-model.md     # 模型文档
├── pyproject.toml        # 项目配置
├── .python-version       # pyenv 版本锁定 (3.12.8)
└── .gitignore
```

## 开发

```bash
# 激活环境
source .venv/bin/activate

# 运行测试
python -m pytest tests/ -v

# 运行示例
python examples/demo.py
```

---

## AI Agent Skill

本项目自带 VS Code Copilot Skill 文件，让 AI Agent 能直接调用智谱免费模型。

### 自动生效

如果你在 VS Code 中打开了此项目，`.copilot/skills/zhipu-free/SKILL.md` 会自动被 Copilot 识别。

### 全局安装

如果希望在所有项目中都可用，复制到用户级别：

```bash
mkdir -p ~/.copilot/skills/zhipu-free
cp .copilot/skills/zhipu-free/SKILL.md ~/.copilot/skills/zhipu-free/
```

之后，Copilot 在任何工作区都能识别“调用智谱模型”类请求，自动通过 `zhipu` CLI 执行。

---

## License

MIT
