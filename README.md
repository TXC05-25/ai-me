# AI-Me · 让面试官用对话的方式了解我

> 一个 AI 数字分身（AI Digital Twin）项目 —— 面向 27 届校招面试官的「对话式作品集」
> 候选人用这个项目向面试官介绍自己，同时项目本身就在证明候选人的工程能力。

> 🎯 目标受众：27 届校招 / 暑期实习面试官（LLM 应用工程师 / AI 应用开发工程师方向）

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/TXC05-25/ai-me?style=social)](https://github.com/TXC05-25/ai-me)

<div align="center">

🌐 在线体验：<http://218.244.140.70:5500>（HTTP，临时在阿里云 ECS 上） · 联系：<523589995@qq.com>

</div>

***

## 🎯 项目目标

| 痛点 | 解决方式 |
| --- | --- |
| 校招面试官每天看几百份简历，记不住候选人细节 | AI 数字分身 7×24 在线，基于知识库精准回答 |
| 应届生准备自我介绍 PPT 太耗时且不差异化 | 一份结构化 YAML + Markdown 即可驱动 |
| 应届生想用项目证明自己，又怕面试官没时间看代码 | 项目本身就是作品集（meta portfolio） |
| 校招面试官想问技术深度但不知道问什么 | AI 反向推荐问题，引导面试官深入考察 |

一句话：把「我是谁、我做过什么、我会什么」交给一个能精准回答、且技术深度可见的 AI 系统。

> 📊 **校招 vs 社招定位差异**：本项目以校招视角优化（基础扎实 + 学习速度 + 实习亮点），不堆"主导 X 系统日均 Y 千万请求"类社招话术。

***

## ✨ 功能特性

### 🧠 AI 智能问答（核心）

- **基于 RAG 的精准回答** —— 3 路并发混合检索（向量 + BM25 + 关键词衍生）
- **⟪n⟫ 引用溯源** —— 每条事实标注来源编号，可点击跳转到原始资料
- **流式 SSE 输出** —— 首 token < 1s，逐字呈现回答过程
- **多轮对话记忆** —— 支持「再问一个相关问题」「那段实习具体做什么」等追问
- **意图路由（5 类）** —— `profile_qa` / `project_detail` / `skill_assessment` / `small_talk` / `meta_question`

### ⏱ 真实延迟可视化（借鉴 Kushal9889/kushal-portfolio-v2）

- 每条 AI 回答下方显示 ⏱ 意图 / 🔍 检索 / 📊 重排 / ✨ 生成 / ⚡ 首 token / ⏰ 总耗时
- `/metrics` 端点返回 P50 / P95 / P99 延迟、token 速率
- Dashboard 页面实时展示全栈延迟统计（每 10s 刷新）

### 📊 RAGAS 评估可视化（借鉴 dangogit/tookai-ai）

- 6 项指标雷达图（手写 SVG）：faithfulness / answer_relevancy / context_precision 等
- `/metrics/eval` 端点返回评估分数

### 🎯 CTA 按钮 + 简历下载（借鉴 Hillariaa/ai-automation-agent）

- 顶部导航：「📄 简历」「✉️ 联系」一键触达
- Hero + Footer：3 处 CTA，让面试官随时行动
- 快捷问题 chips：初始消息预置示例问题，一键提问

### 🎨 极简 AMA 设计（借鉴 efekucuk/aifolio）

- 克制配色：单一主色 + 黑/白/灰
- 现代排版：sans-serif 主体 + Menlo 等宽字体用于技术元素
- 大量留白：避免视觉噪音

> 📘 详细借鉴清单：[docs/BORROWED_FEATURES.md](docs/BORROWED_FEATURES.md)

### 🛠️ 面试官增强工具

- **「推荐下一个问题」按钮** —— AI 主动建议值得深入考察的方向
- **「一键生成面试脚本」** —— 输入岗位 JD，自动生成 10 道定制化面试题
- **「导出对话记录」** —— 一键导出当前会话为 Markdown，方便后续复盘
- **「简历下载」** —— 顶部悬浮按钮，提供 PDF 简历 + 在线版两个版本

### 🎨 现代化前端

- Hero 主页 + 内嵌聊天窗口 —— 访客无需切换页面即可提问
- 项目卡片网格 —— 所有项目以卡片形式可视化展示，可点击展开技术栈 + 源码链接
- 时间线 + 技能雷达图 —— 教育和项目经历可视化
- 响应式 + 暗色主题 —— 移动端可用，面试官晚上用也不会刺眼
- 零依赖部署 —— 纯静态 HTML + CDN，单文件即可托管

### 🔬 工程化能力（面试考察重点）

- LangSmith 全链路追踪 —— 所有 LLM 调用可视化追踪
- RAGAS 评估脚本 —— 6 项指标量化问答质量
- 请求级 + 全局双日志 —— 便于排查线上问题
- 三级失败回退 —— Rerank / 检索 / 生成多层兜底
- Docker 一键部署 —— `bash deploy.sh` 即可启动完整服务
- 速率限制 + 输入清洗 —— 防注入、防滥用

***

## 🏗️ 技术栈

### 后端

| 模块 | 选型 | 说明 |
| --- | --- | --- |
| Web 框架 | FastAPI | 异步高性能，自动 OpenAPI 文档 |
| Agent 编排 | LangGraph | 状态图编排，可视化调试 |
| LLM | DeepSeek-V3（`deepseek-chat`）| OpenAI 兼容接口，中文友好，成本低 |
| Embedding | OpenAI 兼容服务（默认 `text-embedding-3-small`）| 也可换智源 BGE / Cohere 等 |
| 向量库 | ChromaDB（嵌入式）| 纯 Python，零 native 依赖，自动持久化 |
| 重排 | BGE-Reranker-v2-m3（SiliconFlow）| 提升检索精度 |
| 追踪 | LangSmith | 全链路可观测性 |
| 评估 | RAGAS | 6 项核心指标 |

> 🔧 **可替换性**：LLM / Embedding / Rerank 都按 OpenAI 兼容协议抽象，`.env` 改一个 `BASE_URL` 就能切到任意国内大模型。

### 前端

| 模块 | 选型 | 说明 |
| --- | --- | --- |
| 页面 | 纯 HTML + TailwindCSS（CDN）| 零构建，秒级部署 |
| 交互 | Vanilla JS + Fetch + EventSource | 无框架依赖 |
| 动效 | CSS 动画 | 顺滑不浮夸 |
| 图标 | 内联 SVG | 简洁一致 |
| 部署 | Nginx / 任何静态服务器 | 一份 `frontend/` 即可 |

> 设计原则：后端体现工程深度，前端体现审美与产品思维，两者结合就是候选人最有力的「作品集」。

***

## 📂 目录结构

```
ai-me/
├── README.md                      # 本文件 — 面试官第一眼看到的
├── README_HF.md                   # Hugging Face Spaces 部署说明
├── docker-compose.yml             # 一键启动（API + 前端）
├── Dockerfile                     # HF Spaces / 自托管 Docker 镜像
├── backend/Dockerfile             # 用于 docker-compose 构建后端
├── .env.example                   # 环境变量模板
├── requirements.txt               # Python 依赖
├── deploy.sh                      # 阿里云 / 腾讯云 ECS 一键部署脚本
├── deploy-https.sh                # 域名 + HTTPS 部署脚本（Let's Encrypt）
│
├── backend/                       # FastAPI 后端
│   ├── main.py                    # ⭐ 路由编排（精简版）
│   ├── config.py                  # 全局配置（LLM/向量库/Prompt）
│   ├── models.py                  # ⭐ Pydantic 数据模型（独立）
│   ├── data/                      # 候选人知识库（修改这里就能改变 AI 回答）
│   │   ├── profile.yaml           # ⭐ 个人信息结构化数据
│   │   ├── resume.md              # ⭐ 简历全文
│   │   ├── projects/              # 每个项目一份 Markdown 详情
│   │   │   ├── ai_me.md           # 当前项目（AI-Me 数字分身）
│   │   │   └── rag_graph.md       # RAG 客服问答系统（LangGraph 版）
│   │   └── qa_pairs.jsonl         # ⭐ 高频问答对
│   ├── graph/                     # LangGraph 状态图
│   │   ├── state.py               # 共享状态 TypedDict
│   │   ├── graph.py               # 图结构（精简）
│   │   ├── meta.py                # ⭐ 项目元信息文档（独立避免循环依赖）
│   │   ├── intention_router.py    # 5 类意图路由（Tool Calling）
│   │   └── nodes/                 # ⭐ 节点按职责拆分
│   │       ├── intent.py          # 意图分类
│   │       ├── retrieve.py        # 检索链（rewrite/retrieve/rerank/assemble_context）
│   │       ├── response.py        # 响应（generate/chat/meta）
│   │       └── recommend.py       # 推荐问题
│   └── utils/
│       ├── common.py              # ⭐ 共享工具
│       ├── loader.py              # 多格式文档加载 + ChromaDB 向量化
│       ├── chunker.py             # Block 级文本分块
│       ├── retriever.py           # 3 路并发混合检索
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
│   ├── assets/app.js              # 前端逻辑：Fetch + EventSource
│   └── public/resume.pdf          # 候选人简历 PDF（不进 git）
│
├── eval/                          # 评估
│   ├── eval_dataset.jsonl         # 评估数据集（20+ 问答对）
│   └── run_eval.py                # RAGAS 评估脚本
│
├── docs/
│   ├── architecture.md            # 架构详细说明
│   ├── QUICKSTART.md              # 5 分钟本地跑起来
│   ├── DEPLOYMENT.md              # HF / Vercel 部署
│   ├── CLOUD_DEPLOY.md            # 云服务器部署（阿里云 / 腾讯云）
│   ├── BORROWED_FEATURES.md       # 借鉴清单
│   ├── GITHUB_PROFILE_README.md   # 个人主页 README 模板
│   └── interview_qa.md            # 候选人 FAQ 模板
│
└── scripts/
    ├── init_kb.py                 # 重建知识库
    ├── run_smoke.py               # 烟雾测试（11 项无需外部依赖）
    └── dev.bat                    # Windows 一键开发启动
```

***

## 🚀 快速开始

### 1. 克隆与安装依赖

```bash
git clone https://github.com/TXC05-25/ai-me.git
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
# 编辑 .env，至少需要 LLM_API_KEY + EMBEDDING_API_KEY + RERANK_API_KEY
```

`.env` 默认配置（**全部按 OpenAI 兼容协议**，可平替任意国内大模型）：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `LLM_API_KEY` + `LLM_BASE_URL` | DeepSeek-V3 | 也可换 MiniMax / 智谱 / 通义 |
| `EMBEDDING_API_KEY` + `EMBEDDING_BASE_URL` | OpenAI | 也可换智源 BGE / Cohere |
| `RERANK_API_KEY` + `RERANK_BASE_URL` | SiliconFlow | BGE-Reranker-v2-m3 |
| `LANGCHAIN_API_KEY` | （可选）| LangSmith 追踪 |

### 4. 准备个人资料

```bash
# 编辑以下文件，填入你自己的信息
backend/data/profile.yaml
backend/data/resume.md
backend/data/projects/*.md
backend/data/qa_pairs.jsonl
```

> 🔐 这些文件**已经在 `.gitignore` 里被排除**，不会泄露到 GitHub 上。

### 5. 重建知识库 + 启动服务

```bash
# 首次启动必须重建知识库（把 profile/resume/projects 向量化进 ChromaDB）
python -m utils.loader

# 启动后端（默认端口 8000）
python backend/main.py
# → http://localhost:8000
# → API 文档：http://localhost:8000/docs

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

打开 <http://localhost:5500>，在聊天框输入「请介绍一下你自己」，看看 AI-Me 如何基于你配置的知识库回答。

> 📘 详细的故障排查见 [docs/QUICKSTART.md](docs/QUICKSTART.md)

***

## 🌐 部署方式

本项目支持三种部署途径，建议优先级如下：

### 1. 阿里云 / 腾讯云 ECS（推荐，国内最快）

完整流程见 [docs/CLOUD_DEPLOY.md](docs/CLOUD_DEPLOY.md)。只需要一条：

```bash
curl -fsSL https://raw.githubusercontent.com/TXC05-25/ai-me/main/deploy.sh -o deploy.sh
sudo bash deploy.sh
```

脚本会：装 Docker → 拉代码 → 初始化数据 → 启容器 → 等健康检查。

之后改代码：

```bash
# 本地改完
git add -A && git commit -m "fix: ..."
git push

# 服务器一行重新部署
ssh root@你的IP "cd /opt/ai-me && bash deploy.sh"
```

### 2. Hugging Face Spaces（免费，海外友好）

完整流程见 [README_HF.md](README_HF.md)。

免费额度：~16 小时/天（够用，重启间隔较长）。如果要更稳定：HF Pro $9/月。

### 3. Vercel + HF 分离部署

前端静态部署到 Vercel，后端部署到 HF，通过 `vercel.json` 反代 `/chat/*` 到 HF。

适用于「不想买 ECS、想用现成 CDN」的场景。

***

## 🆕 版本变更记录

### v1.3（最新 · 部署上线）

- ✅ **真实部署到阿里云 ECS**：5184-244-140-70:5500 公开访问
- ✅ **deploy.sh 支持国内镜像**：apt 装 docker、daocloud 镜像源，GFW 友好
- ✅ **Dockerfile 修两个 bug**：WORKDIR 切到 `/app/backend`、`requirements.txt` 路径修正
- ✅ **新增 `.gitattributes`**：强制 LF 行尾，Linux 跑 `bash deploy.sh` 不报 `\r` 错误
- ✅ **新增 `deploy-https.sh`**：支持 Let's Encrypt 自动 HTTPS

### v1.2

- ✅ 修复 `yaml_to_markdown` 丢字段 bug
- ✅ 校园经历知识库完整入库

### v1.1

- ✅ LLM 切到 DeepSeek-V3（成本下降 90%）
- ✅ 向量库切到 ChromaDB（零 Docker 运维）
- ✅ 后端默认端口改为 8000（HF 部署时通过 ENV 覆盖为 7860）

***

## 🎬 演示对话

> 📹 在线 Demo：<http://218.244.140.70:5500>

### 示例 1：项目细节追问

```
👤 面试官：你这个 AI-Me 项目里，意图路由为什么用 Tool Calling 而不是提示词？

🤖 AI：候选人选择 Tool Calling 是因为⟪1⟫：

   1. **结构化输出** —— Tool Calling 强制 LLM 按 JSON Schema 输出，
      避免了提示词里"请按这样输出"的不确定性
   2. **延迟更低** —— Tool Calling 走模型原生路径，比提示词约束少 1-2 次前向
   3. **易于调试** —— 5 类意图变成 5 个 enum 值，日志与评估都更直接

   5 类意图：profile_qa / project_detail / skill_assessment / small_talk / meta_question ⟪1⟫

💡 推荐追问：
   1. 候选人的 3 路并发检索（向量 + BM25 + 关键词衍生）是怎么融合排序的？
   2. 如果 LLM 把"你做过的项目"误识别为 small_talk，你们怎么处理？
```

### 示例 2：实习追问

```
👤 面试官：你在杭州亿渡网络科技实习主要做什么？

🤖 AI：候选人在杭州亿渡网络科技有限公司做 AI 应用开发实习生（2026.07 - 至今）⟪1⟫。

   主要工作：
   - 跟进 RAG + LangGraph 方向的 AI 应用
   - 对接真实业务场景（亿渡是 AI Agent 方向的创业团队）
   - 参与需求评审 / 技术选型 / 代码 review 的完整研发流程
   - 实习期间也独立完成了 RAG 客服问答系统（LangGraph 版 · Block 级架构），召回率提升 28%，准确率提升 35% ⟪1⟫

💡 推荐追问：
   1. 你在实习中最有挑战的一个技术决策是什么？
   2. 「Block 级细粒度检索」具体怎么实现的？
```

### 示例 3：工程能力

```
👤 面试官：你们的 RAG 召回率提升 28% 是怎么测出来的？

🤖 AI：召回率提升的测试方法是⟪1⟫：

   1. **基准集**：准备 50 个真实馆员问询 + ground truth（标注出应被检索到的 block）
   2. **基线版本**：纯向量检索（只用 `top_k=10`）
   3. **改进版本**：向量 + BM25 + 关键词衍生 3 路并发 + BGE-Reranker 重排
   4. **指标**：Recall@10 = 命中 ground truth 的查询占比

   实测：基线 0.62 → 改进 0.79，即 +28%。

💡 推荐追问：
   1. 关键词衍生那一路，你们是用什么模型做的 query 改写？
   2. BGE-Reranker 用了 v2-m3 哪个尺寸？对延迟影响大吗？
```

***

## 🛣️ Roadmap

### v1.x（已完成）

- [x] 基础 RAG 问答（5 类意图路由 + 引用标注 + 流式输出）
- [x] 现代化前端（Hero + 聊天 + 项目卡片 + 暗色主题）
- [x] LangSmith 追踪 + RAGAS 评估
- [x] LLM 切到 DeepSeek-V3（成本下降 90%）
- [x] 向量库切到 ChromaDB（零 Docker 运维）
- [x] 部署到阿里云 ECS 并公网可访问
- [x] 国内网络友好的镜像源配置

### v2.0（计划中）

- [ ] HTTPS + 正式域名（脱离临时 IP）
- [ ] 「面试官模式」—— 输入岗位 JD，自动生成 10 道定制面试题
- [ ] 「语音问答」—— Whisper + Edge-TTS
- [ ] 「项目演示录屏」—— 每个项目嵌入 2 分钟演示视频
- [ ] 多语言支持 —— 中英双语切换

### v3.0（远期）

- [ ] 「AI 模拟面试」—— 候选人主动训练用
- [ ] GitHub 实时同步 —— README / 项目信息自动拉取
- [ ] 「互动编程题」—— 嵌入式 Code Runner

***

## 🤝 设计哲学

> 「项目本身就是最好的简历」

这个项目想要表达的不是「我会做 AI 应用」，而是：

1. **工程化思维**：日志、监控、评估、容错、回退、部署 —— 一个都不能少
2. **产品思维**：考虑面试官的体验（流式、引用、可追问）
3. **审美能力**：前端不能丑，候选人审美也是面试官考察点
4. **持续迭代**：Roadmap 是真实的，不是为了好看而写的
5. **能交付上线**：不只跑通 demo，还能扛住公网真实流量

如果一个面试官愿意花 5 分钟和我这个 AI 对话，他/她大概率比看 5 分钟简历能了解更多关于我的真实信息。

***

## 📜 License

MIT © 2025 txc

***

<div align="center">

如果这个项目给了你灵感，请点个 ⭐️

Made with ❤️ and ☕ by [txc](https://github.com/TXC05-25)

</div>
