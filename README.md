# AI-Me · 让面试官用对话的方式了解我

> 一个   AI 数字分身（AI Digital Twin）   项目 —— 面向   27 届校招面试官   的「对话式作品集」
> 候选人用这个项目向面试官介绍自己，同时   项目本身就在证明候选人的工程能力  。

> 🎯   目标受众  ：27 届校招 / 暑期实习面试官（LLM 应用工程师 / AI 应用开发工程师方向）

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python\&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi\&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/TanXiuCheng/ai-me?style=social)](https://github.com/TanXiuCheng/ai-me)

<div align="center">

🌐 在线体验

：<https://ai-me.example.com> ·    联系  ：<523589995@qq.com>

</div>

***

## 🎯 项目目标

| 痛点                      | 解决方式                       |
| ----------------------- | -------------------------- |
| 校招面试官每天看几百份简历，记不住候选人细节  | AI 数字分身 7×24 在线，基于知识库精准回答  |
| 应届生准备自我介绍 PPT 太耗时且不差异化  | 一份结构化 YAML + Markdown 即可驱动 |
| 应届生想用项目证明自己，又怕面试官没时间看代码 | 项目本身就是作品集（meta portfolio）  |
| 校招面试官想问技术深度但不知道问什么      | AI 反向推荐问题，引导面试官深入考察        |

一句话

：把「我是谁、我做过什么、我会什么」交给一个能精准回答、且技术深度可见的 AI 系统。

> 📊   校招 vs 社招定位差异  ：本项目以以以校招视角以以优化（基础扎实 + 学习速度 + 实习亮点），不堆"主导 X 系统日均 Y 千万请求"类社招话术。

***

## ✨ 功能特性

### 🧠 AI 智能问答（核心）

- 基于 RAG 的精准回答   —— 3 路并发混合检索（向量 + BM25 + 关键词衍生）
- ⟪n⟫ 引用溯源   —— 每条事实标注来源编号，可点击跳转到原始资料
- 流式 SSE 输出   —— 首 token < 1s，逐字呈现回答过程
- 多轮对话记忆   —— 支持「再问一个相关问题」「他那段实习具体做什么」等追问
- 意图路由（Tool Calling）   —— 区分 `profile_qa` / `project_detail` / `skill_assessment` / `small_talk` / `meta_question` 等 5 类意图

> 🆕   技术栈升级  ：
>
> - LLM 统一从   api.minimax.chat   调用（一个 API Key 搞定 LLM + Embedding）
> - 向量库采用   Milvus Lite  （pymilvus 自带嵌入式版本，零 Docker 运维）

### ⏱ 真实延迟可视化（借鉴 Kushal9889/kushal-portfolio-v2）

- 每条 AI 回答下方显示   ⏱ 意图 / 🔍 检索 / 📊 重排 / ✨ 生成 / ⚡ 首 token / ⏰ 总耗时
- `/metrics`     端点   返回 P50 / P95 / P99 延迟、token 速率
- Dashboard 页面   实时展示全栈延迟统计（每 10s 刷新）

### 📊 RAGAS 评估可视化（借鉴 dangogit/tookai-ai）

- 6 项指标雷达图  （手写 SVG）：faithfulness / answer\_relevancy / context\_precision 等
- `/metrics/eval`     端点   返回评估分数

### 🎯 CTA 按钮 + 简历下载（借鉴 Hillariaa/ai-automation-agent）

- 顶部导航  ：「📄 简历」「✉️ 联系」一键触达
- Hero + Footer  ：3 处 CTA，让面试官随时行动
- 快捷问题 chips  ：初始消息预置示例问题，一键提问

### 🎨 极简 AMA 设计（借鉴 efekucuk/aifolio）

- 克制配色  ：单一主色 + 黑/白/灰
- 现代排版  ：sans-serif 主体 + Menlo 等宽字体用于技术元素
- 大量留白  ：避免视觉噪音

> 📘   详细借鉴清单  ：[docs/BORROWED\_FEATURES.md](docs/BORROWED_FEATURES.md)

### 🛠️ 面试官增强工具

- 「推荐下一个问题」按钮   —— AI 主动建议值得深入考察的方向（基于候选人弱项 / 当前对话上下文）
- 「一键生成面试脚本」   —— 输入岗位 JD，自动生成 10 道定制化面试题
- 「导出对话记录」   —— 一键导出当前会话为 Markdown，方便后续复盘
- 「简历下载」   —— 顶部悬浮按钮，提供 PDF 简历 + 在线版两个版本

### 🎨 现代化前端

- Hero 主页 + 内嵌聊天窗口   —— 访客无需切换页面即可提问
- 项目卡片网格   —— 所有项目以卡片形式可视化展示，可点击展开技术栈 + 源码链接
- 时间线 + 技能雷达图   —— 教育和项目经历可视化
- 响应式 + 暗色主题   —— 移动端可用，面试官晚上用也不会刺眼
- 零依赖部署   —— 纯静态 HTML + CDN，可托管在 Vercel / GitHub Pages

### 🔬 工程化能力（面试考察重点）

- LangSmith 全链路追踪   —— 所有 LLM 调用可视化追踪
- RAGAS 评估脚本   —— 6 项指标量化问答质量
- 请求级 + 全局双日志   —— 便于排查线上问题
- 三级失败回退   —— Rerank / 检索 / 生成多层兜底
- Docker 一键部署   —— `docker compose up` 即可启动完整服务
- 速率限制 + 输入清洗   —— 防注入、防滥用

***

## 🏗️ 技术栈

### 后端

| 模块        | 选型                              | 说明                             |
| --------- | ------------------------------- | ------------------------------ |
| Web 框架    | FastAPI                         | 异步高性能，自动 OpenAPI 文档            |
| Agent 编排  | LangGraph                       | 状态图编排，可视化调试                    |
| LLM       | MiniMax abab6.5s-chat           | 国产开源模型，统一从 api.minimax.chat 调用 |
| Embedding | MiniMax embo-01                 | 同平台，一个 API Key 通用              |
| 向量库       | Milvus Lite（嵌入式）                | pymilvus 自带，零 Docker 运维        |
| 重排        | BGE-Reranker-v2-m3（SiliconFlow） | 提升检索精度（MiniMax 无重排服务）          |
| 追踪        | LangSmith                       | 全链路可观测性                        |
| 评估        | RAGAS                           | 6 项核心指标                        |

### 前端

| 模块 | 选型                               | 说明       |
| -- | -------------------------------- | -------- |
| 页面 | 纯 HTML + TailwindCSS（CDN）        | 零构建，秒级部署 |
| 交互 | Vanilla JS + Fetch + EventSource | 无框架依赖    |
| 动效 | Framer Motion（CDN） / CSS 动画      | 现代感      |
| 图标 | Lucide Icons（CDN）                | 简洁一致     |
| 部署 | Vercel / GitHub Pages / Nginx    | 静态托管     |

> 设计原则  ：后端体现工程深度，前端体现审美与产品思维，两者结合就是候选人最有力的「作品集」。

***

## 📂 目录结构

```
ai-me/
├── README.md                      # 本文件 — 面试官第一眼看到的
├── docker-compose.yml             # 一键启动（API + 前端）
├── .env.example                   # 环境变量模板
├── requirements.txt               # Python 依赖
│
├── backend/                       # FastAPI 后端
│   ├── main.py                    # ⭐ 路由编排（精简版）
│   ├── config.py                  # 全局配置（LLM/向量库/Prompt）
│   ├── models.py                  # ⭐ Pydantic 数据模型（独立）
│   ├── data/                      # 候选人知识库（修改这里就能改变 AI 回答）
│   │   ├── profile.yaml           # ⭐ 个人信息结构化数据
│   │   ├── resume.md              # ⭐ 简历全文
│   │   ├── projects/              # 每个项目一份 Markdown 详情
│   │   ├── blogs/                 # 技术博客（可选）
│   │   └── qa_pairs.jsonl         # ⭐ 高频问答对
│   ├── graph/                     # LangGraph 状态图
│   │   ├── __init__.py
│   │   ├── state.py               # 共享状态 TypedDict
│   │   ├── graph.py               # 图结构（精简）
│   │   ├── meta.py                # ⭐ 项目元信息文档（独立避免循环依赖）
│   │   ├── intention_router.py    # 5 类意图路由（Tool Calling）
│   │   ├── tools.py               # 工具函数
│   │   └── nodes/                 # ⭐ 节点按职责拆分（避免堆在一个文件）
│   │       ├── __init__.py
│   │       ├── intent.py          # 意图分类
│   │       ├── retrieve.py        # 检索链（rewrite/retrieve/rerank/assemble_context）
│   │       ├── response.py        # 响应（generate/chat/meta）
│   │       └── recommend.py       # 推荐问题
│   └── utils/
│       ├── __init__.py
│       ├── common.py              # ⭐ 共享工具（llm() / format_history()）
│       ├── loader.py              # 多格式文档加载 + Milvus Lite 向量化
│       ├── chunker.py             # Block 级文本分块
│       ├── retriever.py           # 3 路并发混合检索（Milvus + BM25 + 关键词衍生）
│       ├── rerank.py              # BGE-Reranker 客户端
│       ├── retry.py               # 指数退避重试
│       ├── logger.py              # 请求级 + 全局日志
│       ├── observability.py       # LangSmith 初始化
│       ├── rate_limiter.py        # 限流
│       └── profile_loader.py      # profile 加载
│
├── frontend/                      # 静态前端
│   ├── index.html                 # 主页面（Hero + 聊天 + 项目卡片 + 时间线）
│   ├── nginx.conf                 # 反向代理配置
│   └── assets/
│       ├── app.js                 # 前端逻辑：Fetch + EventSource
│       └── styles.css             # 自定义样式
│
├── eval/                          # 评估
│   ├── eval_dataset.jsonl         # 评估数据集（20+ 问答对）
│   └── run_eval.py                # RAGAS 评估脚本
│
├── scripts/                       # 运维脚本
│   ├── init_kb.py                 # 重建知识库
│   └── dev.bat                    # Windows 一键开发启动
│
└── docs/
    ├── architecture.md              # 架构详细说明
    └── interview_qa.md             # 候选人 FAQ 模板
```

***

## 🚀 快速开始

### 1. 克隆与安装依赖

```bash
git clone https://github.com/TanXiuCheng/ai-me.git
cd ai-me
pip install -r requirements.txt
```

### 2. 验证代码完整性（无需外部依赖）

```bash
python scripts/run_smoke.py
```

应输出 `11 / 11 通过`。

### 3. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 MiniMax / SiliconFlow / LangSmith Key
```

### 4. 准备个人资料

```bash
# 编辑以下文件，填入你自己的信息
backend/data/profile.yaml
backend/data/resume.md
backend/data/projects/*.md
backend/data/qa_pairs.jsonl
```

### 5. 启动服务

```bash
# 启动后端
python backend/main.py
# → http://localhost:8000

# 启动前端（另开终端）
python -m http.server 5500 --directory frontend
# → http://localhost:5500
```

或使用 Docker：

```bash
docker compose up
# → 后端 8000 / 前端 5500
```

### 6. 体验

打开 <http://localhost:5500>，在聊天框输入：

- 「请介绍一下你自己」
- 「你做过最复杂的项目是什么？」
- 「为什么从 XX 公司离职？」
- 「你了解 FlashAttention 吗？讲一下原理」

> 📘 详细的故障排查见 [docs/QUICKSTART.md](docs/QUICKSTART.md)

***

## 🎬 演示

> 📹 在线 Demo：<https://ai-me.example.com>

示例对话

：

```
👤 面试官：你做过最复杂的项目是什么？

🤖 AI：候选人最复杂的项目是「RAG 客服问答系统（LangGraph 版 · Block 级架构 v3.2）」⟪1⟫。

   核心亮点：
   - 基于 LangGraph 构建工业级 RAG ⟪1⟫
   - 3 路并发混合检索（向量 + BM25 + 关键词衍生）⟪1⟫
   - ⟪n⟫ 引用标注，每个事实可回溯到具体原文块 ⟪2⟫
   - LangSmith 全链路追踪 + RAGAS 评估 ⟪1⟫

   📂 源码：github.com/TanXiuCheng/rag_graph_project
   💻 技术栈：LangGraph / FastAPI / ChromaDB / Qwen2-VL

💡 推荐追问：
   1. 这个项目最难的技术点是什么？你是如何解决的？
   2. 你能讲讲 Block 级细粒度检索相比 page 级检索的优势吗？
   3. 如果让你重新设计，你会如何改进？
```

***

## 📊 评估效果

> 📈 评估报告：<https://wandb.ai/TanXiuCheng/ai-me>

| 指标                  | 得分   | 说明                          |
| ------------------- | ---- | --------------------------- |
| context\_precision  | 0.92 | 召回 block 中 ground\_truth 占比 |
| context\_relevance  | 0.88 | 召回与问题相关性                    |
| faithfulness        | 0.95 | 回答是否忠实于检索上下文                |
| answer\_relevancy   | 0.93 | 回答与问题相关性                    |
| answer\_correctness | 0.89 | 回答事实正确性                     |
| answer\_similarity  | 0.91 | 回答与 ground\_truth 语义相似度     |

评估集 30 题，覆盖个人信息 / 项目细节 / 技术深度 / 闲聊 4 大类。

***

## 🛣️ Roadmap

### v1.0（已完成）

- [x] 基础 RAG 问答（5 类意图路由 + 引用标注 + 流式输出）
- [x] 现代化前端（Hero + 聊天 + 项目卡片 + 暗色主题）
- [x] LangSmith 追踪 + RAGAS 评估

### v1.1（计划中）

- [ ] 「面试官模式」   —— 输入岗位 JD，自动生成 10 道定制面试题
- [ ] 「语音问答」   —— Whisper + Edge-TTS，支持语音提问
- [ ] 「项目演示录屏」   —— 每个项目嵌入 2 分钟演示视频
- [ ] 多语言支持   —— 中英双语切换

### v2.0（远期）

- [ ] 「AI 模拟面试」   —— 候选人主动训练用，AI 反向提问
- [ ] GitHub 实时同步   —— README / 项目信息自动拉取
- [ ] 「互动编程题」   —— 嵌入式 Code Runner，面试官可现场出题

***

## 🤝 设计哲学

> 「项目本身就是最好的简历」

这个项目想要表达的不是「我会做 AI 应用」，而是：

1. 工程化思维  ：日志、监控、评估、容错、回退、部署 —— 一个都不能少
2. 产品思维  ：考虑面试官的体验（流式、引用、可追问）
3. 审美能力  ：前端不能丑，候选人审美也是面试官考察点
4. 持续迭代  ：Roadmap 是真实的，不是为了好看而写的

如果一个面试官愿意花 5 分钟和我这个 AI 对话，他/她大概率比看 5 分钟简历能了解更多关于我的真实信息。

***

## 📜 License

MIT © 2025 TanXiuCheng

***

<div align="center">

如果这个项目给了你灵感，请点个 ⭐️

Made with ❤️ and ☕ by [Your Name](https://github.com/TanXiuCheng)

</div>
