# 🚀 AI-Me 部署指南

> 把 AI-Me 部署到公网，让面试官能直接访问

---

## 📐 架构

```
┌─────────────────────────────────────────┐
│  Vercel（前端，全球 CDN，免费）            │
│  https://ai-me-xxxx.vercel.app          │
│  ↓ 反向代理                              │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Hugging Face Spaces（后端，免费 24/7）   │
│  https://<you>-ai-me.hf.space           │
│  FastAPI + LangGraph + Milvus Lite      │
└─────────────────────────────────────────┘
```

**为什么这样拆？**
- **Vercel**：全球 CDN，静态资源秒加载，免费额度大
- **Hugging Face Spaces**：Python 后端最友好的免费平台（Docker 运行时，免运维）
- **域名**：用 Vercel 分配的 `<project>.vercel.app` 即可（无需买域名）

---

## 🚀 部署步骤

### Step 1：Fork 项目到你的 GitHub

1. 把 `ai-me/` 项目推到你的 GitHub 仓库（如 `github.com/<your-name>/ai-me`）
2. 仓库设为 **Public**（Vercel / HF 都要读）

### Step 2：部署后端到 Hugging Face Spaces

#### 2.1 创建 Space
1. 访问 <https://huggingface.co/new-space>
2. 填写：
   - **Space name**：`ai-me`（URL 会是 `<your-hf-name>-ai-me.hf.space`）
   - **License**：MIT
   - **Space SDK**：**Docker**
   - **Space hardware**：**CPU basic - free**（校招 demo 够用）
   - **Visibility**：**Public**

#### 2.2 上传代码（两种方式任选）

**方式 A：Git push（推荐）**
```bash
# 在你的项目根目录
git remote add hf https://huggingface.co/spaces/<your-hf-name>/ai-me
git add backend/ Dockerfile README_HF.md requirements.txt .dockerignore
git commit -m "Deploy AI-Me to HF Spaces"
git push hf main
```

**方式 B：网页上传**
- 在 Space 页面 → Files → Upload files
- 把 `backend/`、`Dockerfile`、`README_HF.md`、`requirements.txt` 全部上传

#### 2.3 配置 Secrets
在 Space 页面 → **Settings** → **Variables and secrets**，添加：

| Name | Type | Value |
| --- | --- | --- |
| `LLM_API_KEY` | Secret | DeepSeek `sk-xxx` |
| `EMBEDDING_API_KEY` | Secret | OpenAI `sk-xxx`（或其他 Embedding 服务） |
| `RERANK_API_KEY` | Secret | SiliconFlow `sk-xxx` |
| `LANGCHAIN_API_KEY` | Secret | `lsv2_pt_xxx`（可选） |

#### 2.4 等待构建
- HF 自动构建 Docker 镜像（首次 5-10 分钟）
- 完成后访问 `https://<your-hf-name>-ai-me.hf.space`
- 测试 `/docs` 和 `/health`

### Step 3：部署前端到 Vercel

#### 3.1 准备工作
1. 修改 `vercel.json`，把所有 `<YOUR-HF-SPACE>` 替换成你的实际 Space URL
   ```json
   "destination": "https://yourname-ai-me.hf.space/chat/$1"
   ```

2. 修改 `frontend/assets/app.js` 顶部：
   ```js
   const API_BASE = 'https://yourname-ai-me.hf.space';
   // 因为 Vercel 会通过 rewrites 代理，但 app.js 在浏览器端运行
   // 如果前端和后端不同域，需要直接指向 HF 后端
   ```
   
   或者保留相对路径，由 Vercel 的 rewrites 代理：
   ```js
   const API_BASE = '';  // 走 Vercel rewrites
   ```

#### 3.2 部署到 Vercel

**方式 A：网页导入（最简单）**
1. 访问 <https://vercel.com/new>
2. **Import Git Repository**：选择你的 `ai-me` 仓库
3. 配置：
   - **Framework Preset**：Other
   - **Root Directory**：保持默认
   - **Build Command**：留空
   - **Output Directory**：填 `frontend`
4. 点击 **Deploy**
5. 1 分钟后会拿到 `https://ai-me-xxxx.vercel.app`

**方式 B：CLI**
```bash
npm i -g vercel
vercel login
vercel --prod
```

### Step 4：验证

访问你的 Vercel URL：
- ✅ 页面正常加载
- ✅ 聊天框能输入
- ✅ AI 在 3 秒内回复
- ✅ 延迟徽章显示
- ✅ 雷达图渲染

---

## 🎁 部署后给面试官发什么

把这两个链接发给面试官：

```
🌐 项目主页：https://ai-me-xxxx.vercel.app
📚 技术文档：https://github.com/<your-name>/ai-me
```

简历 PDF 链接可以放在：
- 项目主页 Footer 的「📄 简历 PDF」按钮（指向 GitHub raw PDF）
- 邮件正文附件
- LinkedIn

---

## 💰 成本估算

| 平台 | 费用 | 限制 |
| --- | --- | --- |
| Vercel | **$0** | 100GB 流量/月（够用） |
| Hugging Face Spaces CPU basic | **$0** | 16 小时/天运行（空闲会自动 sleep） |
| DeepSeek LLM | ¥1-2/百万 token | 校招 demo 月消耗 < ¥5 |
| OpenAI Embedding | $0.02/百万 token | 重建向量库一次约 $0.001 |
| SiliconFlow Rerank | 免费额度 | |

**总成本：¥5-10/月**（如果面试官偶尔访问）

---

## 🔧 进阶：自定义域名（可选）

如果你有自己的域名（如 `yourname.com`）：

1. **Vercel**：Settings → Domains → 添加 `ai-me.yourname.com`，按提示配置 DNS
2. **HF Spaces**：免费版不支持自定义域名（升级 Pro 可以）

---

## 🐛 部署常见问题

### Q1：HF 构建失败
**A**：查看 Build logs，常见原因：
- 依赖缺失：检查 `requirements.txt`
- 端口错误：HF 必须用 7860（已配置 `ENV APP_PORT=7860`）
- 内存不足：ChromaDB 首次构建索引会占用较多内存，CPU basic 有 16GB 应该够

### Q2：前端 CORS 错误
**A**：HF 后端默认允许所有 CORS（已在 `main.py` 配置）。如果还有问题：
- 确认 `API_BASE` 配置正确
- 检查浏览器 Network → 看请求是否到达 HF

### Q3：HF Spaces 启动慢（30-60s）
**A**：CPU basic 性能较弱 + 首次启动要重建向量库。可以：
- 升级到 CPU upgrade（更快但收费）
- 或用 Railway / Render（启动也快）

### Q4：数据每次重启都丢
**A**：HF Spaces 重启后 `vector_db/` 目录会被清空（除非用 Persistent Storage beta）。
**临时方案**：在 `scripts/init_kb.py` 加个 Web 触发，让用户首次访问时自动构建。
**永久方案**：接 Redis / Postgres / Pinecone。

### Q5：HF 私有 Space 可以吗？
**A**：可以，但 Vercel 代理会失败（HF 私有 Space 需要 Token）。
建议：Space 设 Public，安全靠 Secrets（API Key 不外泄）。

---

## 🚀 部署完成后 5 件事

1. **测试 5 个高频问题**（自我介绍 / 项目 / 实习 / 技术 / 反问）
2. **截图保存**（README 加截图，提升可信度）
3. **LinkedIn 加项目链接**（校招加分）
4. **GitHub Profile README**（让面试官访问 GitHub 第一眼看到）
5. **发给 1-2 个朋友试用**（收集反馈再优化）

---

## 📊 部署 Checklist

- [ ] HF Space 创建成功，状态是 Running
- [ ] HF Secrets 配置完毕（4 个 API Key）
- [ ] `/health` 返回 ok
- [ ] `/chat` 能正常回答
- [ ] Vercel 部署成功，拿到 URL
- [ ] Vercel URL 访问正常
- [ ] 简历 PDF 已上传到 GitHub（让 Vercel 能访问）
- [ ] LinkedIn / 简历 加了项目链接
- [ ] 隐私检查（电话 / 邮箱是否要公开）

---

> 💡 **Tips**：HF Space 启动慢是正常的，建议你**每天早上**打开一次让它 build 完成，面试时直接用。