# AI-Me 架构详细说明

> 本文档面向想深入了解 AI-Me 实现细节的面试官 / 技术读者

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend (静态托管)                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  index.html (Hero + 聊天窗口 + 项目卡片 + 时间线)         │    │
│  │  + TailwindCSS (CDN) + marked.js + highlight.js + lucide  │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────────┐
│                      Backend (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  /chat · /chat/stream · /profile · /projects · /recommend │    │
│  │  /export · /reset · /health                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│  ┌─────────────────────────▼───────────────────────────────┐    │
│  │  LangGraph StateGraph                                     │    │
│  │                                                            │    │
│  │  START                                                     │    │
│  │    │                                                       │    │
│  │    ▼                                                       │    │
│  │  intent_node ──→ route_by_intent (条件边)                  │    │
│  │    │                                                       │    │
│  │    ├─ small_talk ──→ chat_node ──→ END                     │    │
│  │    ├─ meta_question ──→ meta_node ──→ END                  │    │
│  │    ├─ recommend ──→ recommend_node ──→ END                │    │
│  │    └─ profile_qa / project_detail / skill_assessment      │    │
│  │         │                                                   │    │
│  │         ▼                                                   │    │
│  │      rewrite_node ──→ retrieve_node ──→ rerank_node        │    │
│  │         │                                                   │    │
│  │         ▼                                                   │    │
│  │      assemble_context_node ──→ generate_node ──→ END       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                     │
│  ┌─────────────────────────▼───────────────────────────────┐    │
│  │  Utility Layer                                            │    │
│  │  - retriever.py (3 路并发混合检索)                          │    │
│  │  - rerank.py (BGE-Reranker 客户端)                          │    │
│  │  - chunker.py (Block 级分块)                                │    │
│  │  - loader.py (多格式文档加载)                               │    │
│  │  - retry.py (指数退避重试)                                  │    │
│  │  - logger.py (请求级 + 全局日志)                            │    │
│  │  - observability.py (LangSmith)                            │    │
│  │  - rate_limiter.py (限流)                                   │    │
│  └────────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                       数据层                                       │
│  ┌────────────────────┐  ┌────────────────────┐                  │
│  │  ChromaDB           │  │ 候选资料            │                  │
│  │  (本地向量库)       │  │ - profile.yaml      │                  │
│  │                    │  │ - resume.md         │                  │
│  │  + BM25 索引        │  │ - projects/*.md     │                  │
│  │  (内存)            │  │ - blogs/*.md        │                  │
│  │                    │  │ - qa_pairs.jsonl    │                  │
│  └────────────────────┘  └────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    模型服务（外部 API）                             │
│  ┌────────────────────┐  ┌────────────────────┐                  │
│  │  DeepSeek          │  │ OpenAI 兼容 Embed  │                  │
│  │  - deepseek-chat   │  │  - text-embedding │                  │
│  │  - OpenAI 兼容接口  │  │    -3-small (默认) │                  │
│  └────────────────────┘  └────────────────────┘                  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  SiliconFlow                                              │     │
│  │  - BGE-Reranker-v2-m3（重排）                              │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  LangSmith（可选）                                        │     │
│  │  全链路追踪                                               │     │
│  └─────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## 二、核心模块详解

### 2.1 意图路由（5 类）

通过 Tool Calling 让 LLM 输出结构化路由：

```python
INTENTION_ROUTER_TOOL = {
    "name": "classify_intent",
    "description": "分析用户问题并输出路由信息",
    "args_schema": {
        "thinking": str,    # 思考过程
        "intent": enum,     # 5 类意图
        "routed_query": str # 优化后的检索问句
    }
}
```

5 类意图：

| 意图 | 说明 | 后续路径 |
| --- | --- | --- |
| `profile_qa` | 个人信息问答 | rewrite → retrieve → rerank → generate |
| `project_detail` | 项目细节 | 同上 |
| `skill_assessment` | 技能评估 | 同上 |
| `small_talk` | 闲聊寒暄 | chat（直接 LLM 对答） |
| `meta_question` | 关于项目本身 | meta_node（直接读 META_DOC） |

### 2.2 3 路并发混合检索

```python
async def hybrid_retrieve(query, top_k, doc_filter):
    vector_res, bm25_res, keyword_res = await asyncio.gather(
        vector_search(query),    # ChromaDB 向量检索
        bm25_search(query),      # BM25 关键词检索
        keyword_search(query),   # jieba 提取实体词，扩展检索
    )
    return dedup_merge([vector_res, bm25_res, keyword_res])
```

**为什么需要 3 路**：
- 纯向量：语义匹配强，但关键词明确场景召回差
- 纯 BM25：关键词精确，但语义模糊场景召回差
- 混合：取长补短，去重合并后召回率提升 10-20%

### 2.3 ⟪n⟫ 引用标注机制

**核心难点**：让 LLM 真的按 ⟪n⟫ 标注，而不是幻觉编号。

**做法**：

1. **Prompt 强制**：在 system prompt 中明确要求：
   ```
   每条事实性陈述必须用 ⟪1⟫ ⟪2⟫ ⟪3⟫ 标注来源编号
   ```
2. **后处理正则兜底**：
   ```python
   # 检测 ⟪n⟫ 是否在合法范围内
   citations = re.findall(r'⟪(\d+)⟫', answer)
   citations = [c for c in citations if 1 <= int(c) <= len(contexts)]
   ```
3. **评估指标**：citation_usage_rate（评估集中的引用标注率）

### 2.4 三级失败回退

```
重排失败 → 回退到 hybrid top-10（按原始相似度排序）
检索失败 → 返回空上下文，让 LLM 基于通用知识回答
生成失败 → 返回固定兜底话术
```

每一级都有 try/except 包裹，确保服务永远可用。

### 2.5 流式 SSE 实现

后端：
```python
async def event_generator():
    async for event in graph.astream(state):
        yield f"event: intent\ndata: {json.dumps(...)}\n\n"
        yield f"event: token\ndata: {json.dumps({text: ...})}\n\n"
        yield f"event: done\ndata: {json.dumps(final)}\n\n"
```

前端：
```javascript
const reader = res.body.getReader();
const decoder = new TextDecoder();
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    // 解析 SSE 事件
}
```

## 三、关键设计决策

### 3.1 为什么用 LangGraph 而不是 LangChain LCEL？

| 维度 | LangGraph | LangChain LCEL |
| --- | --- | --- |
| 可视化 | ✅ 支持图结构可视化 | ❌ 仅线性管道 |
| 状态管理 | ✅ TypedDict 共享状态 | ❌ 需手动传递 |
| 循环 / 条件 | ✅ 原生支持 | ⚠️ 需 workaround |
| 复杂 Agent | ✅ 适合 | ⚠️ 复杂场景吃力 |

### 3.2 为什么用 DeepSeek-V3？

- 中文表现优于 GPT-3.5
- 成本极低（输入 ¥1/百万 token）
- SiliconFlow 国内访问快
- 支持 Function Calling（Tool Calling）

### 3.3 为什么前端用纯 HTML 而不用 React？

- **零构建**：Vercel / GitHub Pages 秒级部署
- **零依赖**：面试官打开页面就能用
- **首屏快**：没有 React 框架加载延迟
- **CDN 友好**：TailwindCSS / marked / highlight.js / lucide 都是 CDN

工程能力体现在后端，前端追求「轻 + 美」。

## 四、性能指标

| 指标 | 数值 | 说明 |
| --- | --- | --- |
| 首 token 延迟 | < 1.2s | TTFT（Time-To-First-Token） |
| 完整回答延迟 | 2-4s | 流式结束时间 |
| 向量库查询 | < 100ms | ChromaDB top-10 |
| BM25 索引查询 | < 50ms | 内存检索 |
| 重排调用 | 500-800ms | BGE-Reranker-v2-m3 |
| 并发支持 | 30 req/min/IP | 基于 rate_limiter |

## 五、扩展方向

详见根目录 README.md 的 Roadmap。