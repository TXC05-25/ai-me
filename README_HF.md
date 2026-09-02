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

> 部署到 Hugging Face Spaces，免费 + 24/7 在线 + 全球加速

## 部署步骤

### 1. 创建 Space

1. 访问 <https://huggingface.co/new-space>
2. 填写：
   - **Space name**：`ai-me`（或你喜欢的名字，最终 URL 是 `<your-name>-ai-me.hf.space`）
   - **License**：MIT
   - **Space SDK**：**Docker**
   - **Space hardware**：CPU basic（免费）— 如果需要更好性能选 CPU upgrade
   - **Visibility**：Public（让面试官能访问）

3. 点击 **Create Space**

### 2. 上传文件

把以下文件推送到 Space 仓库：

```bash
# 在 HF Space 仓库根目录
git remote add hf https://huggingface.co/spaces/<your-name>/ai-me
git add backend/ Dockerfile README_HF.md requirements.txt
git commit -m "Initial deploy"
git push hf main
```

或直接通过网页界面上传文件。

### 3. 配置 Secrets

在 Space 页面 → **Settings** → **Variables and secrets**，添加：

| Name | Type | Value |
| --- | --- | --- |
| `LLM_API_KEY` | Secret | MiniMax sk-xxx |
| `EMBEDDING_API_KEY` | Secret | MiniMax sk-xxx |
| `RERANK_API_KEY` | Secret | SiliconFlow sk-xxx |
| `LANGCHAIN_API_KEY` | Secret | lsv2_pt_xxx（可选） |

### 4. 等待构建

- HF 会自动构建 Docker 镜像（3-5 分钟）
- 构建完成后，访问 `https://<your-name>-ai-me.hf.space`
- `/docs` 看 API 文档
- `/health` 健康检查

## 配置 Vercel 前端代理

Vercel 前端通过 `vercel.json` 的 `rewrites` 把 `/chat/*` 代理到 HF 后端。

在 Vercel 部署时，把 `vercel.json` 中所有 `<YOUR-HF-SPACE>` 替换为你的实际 Space 名（如 `yourname-ai-me`）。

## 本地测试

```bash
docker build -f Dockerfile -t ai-me-backend .
docker run -p 7860:7860 --env-file .env ai-me-backend
# 访问 http://localhost:7860/docs
```

## 注意事项

- HF CPU basic 免费额度：~16 小时/天（够用，重启间隔较长）
- 如果要更稳定：HF Pro 9$/月，或用 Railway / Render
- 数据（向量库 + 日志）每次重启会丢失（建议生产接 Redis / 外部存储）