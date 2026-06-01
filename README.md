# 神秘塔罗 - 宇宙能量占卜

一个充满神秘气息的塔罗牌占卜网站，使用 FastAPI 后端 + 纯 HTML/CSS/JS 前端构建。

## 特色功能

- **宇宙能量滚动数字** - 每 0.5 秒刷新的随机数字，捕捉命运的瞬间
- **78 张完整塔罗牌** - 包含 22 张大阿卡纳和 56 张小阿卡纳
- **真实卡牌图片** - 使用韦特塔罗牌 (Rider-Waite) 公共领域图片
- **智能抽牌算法** - 基于宇宙能量计算抽取三张牌
- **AI 解读** - 使用 Deepseek API 生成诗意解读
- **实时流式输出** - WebSocket 连接，打字机效果逐字显示解读
- **精美动画** - 星空背景、粒子效果、翻牌动画
- **响应式设计** - 完美适配各种设备

## 快速开始

### 1. 安装依赖（使用 UV）

```bash
uv sync
```

### 2. 配置 Deepseek API

复制 `.env.example` 为 `.env` 并填入你的 Deepseek API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
```

> `deepseek-chat` 是 Deepseek V4 Pro 的非推理模式
> 如果不配置 API，将使用本地生成的简单解读

### 3. 启动服务

```bash
uv run uvicorn main:app --reload
```

或者：

```bash
uv run python main.py
```

### 4. 访问网站

打开浏览器访问：http://localhost:8000

## 使用方法

1. 观察不断滚动的「宇宙能量」数字
2. 在你感觉命运召唤的瞬间，点击「开启命运之门」
3. 等待宇宙为你抽取三张塔罗牌
4. 阅读命运的解读，获得启示

## 塔罗牌说明

### 大阿卡纳 (Major Arcana)
22 张牌，代表人生重大主题和精神旅程

### 小阿卡纳 (Minor Arcana)
56 张牌，分为四个花色：
- 权杖 (Wands) - 火元素，代表激情、创造力、行动
- 圣杯 (Cups) - 水元素，代表情感、关系、直觉
- 宝剑 (Swords) - 风元素，代表思想、沟通、冲突
- 钱币 (Pentacles) - 土元素，代表物质、金钱、健康

## 技术栈

- **包管理**: UV
- **后端**: FastAPI + Uvicorn + WebSocket
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **AI**: Deepseek API (V4 Pro 非推理模式) 流式输出
- **图片资源**: GitHub 托管的韦特塔罗牌公共领域图片

## 项目结构

```
塔罗牌/
├── main.py              # FastAPI 后端主文件
├── pyproject.toml       # UV 项目配置
├── .env.example        # 环境变量示例
├── README.md           # 项目说明
├── 塔罗牌研究.md        # 塔罗牌研究资料
└── static/
    └── index.html      # 前端页面
```

## 图片来源

塔罗牌图片来自 [lalesleon13-hash/Tarot](https://github.com/lalesleon13-hash/Tarot)，为韦特塔罗牌 (Rider-Waite) 公共领域图片。

## 免责声明

本项目仅供娱乐放松，请理性看待塔罗牌占卜结果。塔罗牌不是科学预测工具，不能替代专业建议。
