# 🚀 AI-Me · 5 分钟跑起来

> 本指南假设你已经在 `C:\Users\谭修诚\Desktop\ai-me\` 目录。

## ✅ 前置条件检查

```powershell
# 1. Python ≥ 3.10
python --version

# 2. pip ≥ 23
pip --version

# 3. 已有的依赖
pip show fastapi langchain langgraph pydantic jieba rank-bm25 httpx | Select-Object Name, Version
```

如果显示大部分都已有，只缺 `pymilvus` 和 `loguru`，继续下一步。

---

## 📦 第一步：安装缺失依赖

```powershell
cd C:\Users\谭修诚\Desktop\ai-me

# 安装两个核心缺失依赖
pip install pymilvus loguru

# 可选：安装评估依赖（如果你想跑评估）
pip install ragas datasets

# 可选：安装 LangSmith 追踪
pip install langsmith
```

### 如果 pip 安装失败

**问题 A：`Permission denied` 错误**
```powershell
# 方案 1：用 --user 安装到用户目录
pip install --user pymilvus loguru

# 方案 2：用国内镜像加速
pip install pymilvus loguru -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方案 3：用 conda（如果你用 Anaconda）
conda install -c conda-forge pymilvus
conda install -c conda-forge loguru
```

**问题 B：网络超时**
```powershell
# 用阿里云镜像
pip install pymilvus loguru -i https://mirrors.aliyun.com/pypi/simple/

# 或设置默认镜像
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip install pymilvus loguru
```

---

## 🔑 第二步：配置 API Key

```powershell
# 复制环境变量模板
copy .env.example .env

# 编辑 .env，填入真实 API Key
notepad .env
```

`.env` 中需要填的字段：

```env
# MiniMax（LLM + Embedding）
# 获取：https://api.minimax.chat/user-center/basic-information/interface-key
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
EMBEDDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# SiliconFlow（仅重排服务）
# 获取：https://cloud.siliconflow.cn/account/ak
RERANK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ 其他字段保持默认值即可。`EMBEDDING_DIM` 默认 1536（MiniMax embo-01 的向量维度）。

---

## 📚 第三步：构建知识库

```powershell
cd backend
python -c "from utils.loader import build_knowledge_base; build_knowledge_base(force_rebuild=True)"
```

应该看到类似输出：
```
[INFO] 加载 X 个 Block（profile/resume/projects/blogs/qa_pairs/meta）
[INFO] 共 X 个 Block，开始向量化...
[INFO] ✅ 向量化完成，共 X 个 Block 写入 Milvus
```

**向量库文件位置**：`backend/vector_db/milvus.db`

---

## 🚀 第四步：启动服务

打开两个 PowerShell 窗口：

**窗口 1 — 启动后端**
```powershell
cd C:\Users\谭修诚\Desktop\ai-me\backend
python main.py
```

应该看到：
```
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**窗口 2 — 启动前端**
```powershell
cd C:\Users\谭修诚\Desktop\ai-me\frontend
python -m http.server 5500
```

应该看到：
```
Serving HTTP on 0.0.0.0 port 5500 (http://0.0.0.0:5500/)
```

---

## ✨ 第五步：体验

| 链接 | 说明 |
| --- | --- |
| <http://localhost:5500> | 🌐 AI 数字分身主页 |
| <http://localhost:8000/docs> | 📚 FastAPI 自动生成的 API 文档 |
| <http://localhost:8000/health> | ❤️ 健康检查端点 |
| <http://localhost:8000/profile> | 👤 候选人信息（JSON） |
| <http://localhost:8000/projects> | 🚀 项目列表（JSON） |

**测试对话**（在前端聊天框输入）：
1. `请介绍一下你自己`
2. `你做过最复杂的项目是什么？`
3. `FlashAttention 原理是什么？`
4. `你为什么做这个 AI-Me 项目？`
5. `这个项目用了什么技术栈？`

---

## 🐛 常见问题

### Q1: `ModuleNotFoundError: No module named 'pymilvus'`
A: 没装 pymilvus，运行 `pip install pymilvus`

### Q2: `ModuleNotFoundError: No module named 'loguru'`
A: 没装 loguru，运行 `pip install loguru`

### Q3: `401 Unauthorized` / `Invalid API Key`
A: `.env` 中的 API Key 错误或缺失。检查 `LLM_API_KEY`、`EMBEDDING_API_KEY`、`RERANK_API_KEY` 是否填入有效值。

### Q4: Milvus Lite 启动慢
A: 首次启动会创建索引文件，耗时 5-15 秒。后续启动 < 1 秒。

### Q5: 前端能打开但聊天不工作
A: 打开浏览器开发者工具（F12）→ Console 看错误：
- 如果 `CORS error`：后端没启动或端口不对
- 如果 `Network error`：检查 API_BASE 配置（`app.js` 顶部）

### Q6: 答案质量不好 / 引用不对
A:
1. 检查 `backend/data/qa_pairs.jsonl` 是否填入关键问答
2. 检查 `backend/data/profile.yaml` / `resume.md` 是否填入完整
3. 调整 `config.py` 中的 `MAX_RETRIEVE_BLOCKS`（如改为 15）

### Q7: 想换 LLM 模型
A: 编辑 `.env` 中的 `LLM_MODEL`：
```env
LLM_MODEL=abab6.5s-chat       # 默认，中文表现好
LLM_MODEL=abab7-chat          # 更强（如果有权限）
```

### Q8: 想加 LangSmith 追踪
A: 在 `.env` 中：
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_xxxxx
LANGCHAIN_PROJECT=ai-me
```

---

## 📊 验证清单

跑通后，逐项确认：

- [ ] 后端启动无报错，监听 8000 端口
- [ ] 前端启动无报错，监听 5500 端口
- [ ] 打开 <http://localhost:5500> 看到 Hero 页面
- [ ] 聊天框输入问题，AI 能在 3 秒内回复
- [ ] 回答中有 ⟪1⟫ ⟪2⟫ 引用标注
- [ ] 回答末尾有 💡 推荐问题
- [ ] 切换暗色 / 亮色主题正常
- [ ] 「导出对话」按钮能下载 Markdown
- [ ] 「清空」按钮能清空对话

全部 ✅ = 项目跑通！

---

## 🐳 进阶：Docker 部署

如果你想用 Docker 跑：

```powershell
# 1. 安装 Docker Desktop
# 下载：https://www.docker.com/products/docker-desktop

# 2. 在项目根目录运行
cd C:\Users\谭修诚\Desktop\ai-me
docker compose up

# 3. 访问
# 前端：http://localhost:5500
# 后端：http://localhost:8000
```

---

## 🆘 仍然有问题？

1. 查看后端日志：`backend/logs/app.log`
2. 查看请求日志：`backend/logs/requests.log`
3. 在浏览器开发者工具看前端错误
4. 把错误信息贴给我，我帮你排查