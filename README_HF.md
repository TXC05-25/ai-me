---
title: AI-Me
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: true
license: mit
short_description: 候选人的 AI 数字分身 · 让面试官用对话了解我
---

# AI-Me · 数字分身后端（FastAPI）

> 这是把 AI-Me 部署到 Hugging Face Spaces 的专属说明。
> **国内用户推荐：直接看 [docs/CLOUD_DEPLOY.md](docs/CLOUD_DEPLOY.md) 把后端 + 前端都部署到阿里云 ECS，体验更稳、更快。**
> **海外 / 不方便买 ECS 的同学：用本指南部署到 HF Spaces，免费，但每天约 16 小时。**

## 技术栈

- **LLM**：DeepSeek-V3（`deepseek-chat`，OpenAI 兼容协议）
- **Embedding**：OpenAI 兼容服务（默认 `text-embedding-3-small`，也可换智源 BGE / Cohere）
- **向量库**：ChromaDB（嵌入式，纯 Python）
- **重排**：BGE-Reranker-v2-m3（SiliconFlow）
- **Web 框架**：FastAPI + LangGraph

## 部署步骤

### 1. 创建 Space

1. 访问 <https://huggingface.co/new-space>
2. 填写：
   - **Space name**：`ai-me`（最终 URL 是 `<your-name>-ai-me.hf.space`）
   - **License**：MIT
   - **Space SDK**：**Docker**
   - **Space hardware**：CPU basic（免费）— 需要更好性能选 CPU upgrade
   - **Visibility**：Public
3. 点击 **Create Space**

### 2. 上传文件

把以下文件推送到 Space 仓库（**注意：HF Spaces 是裸的，只用项目根的 Dockerfile，不用 docker-compose**）：

```bash
git remote add hf https://huggingface.co/spaces/<your-name>/ai-me
git add backend/ Dockerfile README_HF.md requirements.txt .dockerignore
git commit -m "Initial deploy"
git push hf main
```

或直接通过网页界面上传文件。

### 3. 配置 Secrets

Space 页面 → **Settings** → **Variables and secrets**，添加：

| Name | Type | 说明 |
| --- | --- | --- |
| `LLM_API_KEY` | Secret | DeepSeek `sk-xxx`（<https://platform.deepseek.com/api_keys>）|
| `EMBEDDING_API_KEY` | Secret | OpenAI `sk-xxx` 或其他 Embedding Key |
| `RERANK_API_KEY` | Secret | SiliconFlow `sk-xxx` |
| `LANGCHAIN_API_KEY` | Secret | `lsv2_pt_xxx`（可选，LangSmith 追踪）|

### 4. 准备个人资料

⚠️ **重要**：HF Spaces 会把仓库完整克隆，所以 `backend/data/profile.yaml`、`backend/data/resume.md`、`backend/data/qa_pairs.jsonl` 和 `backend/data/projects/*.md` 这些**真实信息**

- 不应该 push 到公开 HF Space（会被所有人搜到）
- 需要在 HF Space 的 **`Settings → Files → Upload` 里手动上传**（这部分不会被 Git 公开）

或者你改成"不包含个人资料"的脱敏版本专门给 HF Space 部署使用。

### 5. 等待构建

- HF 会自动构建 Docker 镜像（3-5 分钟）
- 构建完成后，访问 `https://<your-name>-ai-me.hf.space`
- `/docs` 看 API 文档
- `/health` 健康检查

### 6. 前端

HF Spaces 单容器只跑后端。前端部署推荐用 **Vercel**：

- 把根目录 `vercel.json` 中所有 `<YOUR-HF-SPACE>` 替换为你的实际 Space 名（如 `yourname-ai-me`）
- Vercel 自动把 `/chat/*` 反代到 HF 后端
- 前端路径直接 `https://<your-name>.vercel.app`

## 本地测试

```bash
docker build -f Dockerfile -t ai-me-backend .
docker run -p 7860:7860 --env-file .env ai-me-backend
# 访问 http://localhost:7860/docs
```

## ⚠️ 注意事项

- **HF CPU basic 免费额度**：~16 小时/天（够个人用，重启间隔较长）
- **如果要更稳定**：HF Pro $9/月，或改用阿里云 ECS（参考 [docs/CLOUD_DEPLOY.md](docs/CLOUD_DEPLOY.md)）
- **数据持久化**：HF 容器重启会丢向量库，建议生产接外部存储（Redis / S3 等）
- **端口说明**：HF Spaces 强制用 7860，已通过 Dockerfile 里 `ENV APP_PORT=7860` 设置

## 常见问题

- **API 一直转圈** —— 多半是 LLM API Key 错了或欠费，去 DeepSeek 后台查余额
- **Embedding 报 401** —— 检查 `EMBEDDING_API_KEY` 和 `EMBEDDING_BASE_URL` 是否配对
- **Rerank 失败** —— `BGE-Reranker` 在 SiliconFlow 上是单独服务，需要单独申请 Key
- **HF 国内访问慢** —— 建议改用阿里云 ECS，参考项目根目录 `README.md` 的部署章节

## 对比三种部署方案

| 方案 | 成本 | 国内访问 | 数据隐私 | 维护成本 | 推荐 |
|------|------|----------|----------|----------|------|
| **阿里云 ECS** | ¥40-100/月（2C2G）| ⭐⭐⭐ 快 | 完全自管 | ⭐⭐ 中（要 SSH）| ✅ 国内首选 |
| **HF Spaces** | 免费 / $9/月 | ⭐ 经常卡 | HF 托管 | ⭐ 最低 | ✅ 海外首选 |
| **Vercel + HF** | 免费 | ⭐⭐ 一般 | HF 托管 | ⭐ 最低 | 轻量个人版 |
