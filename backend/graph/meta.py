"""
项目元信息文档
==============
用于回答面试官关于项目本身（架构/部署/设计哲学）的问题
独立成文件以避免循环依赖（utils.loader 也要用）
"""

from __future__ import annotations

META_DOC = """
# AI-Me 项目元信息

## 这是什么
面向面试官的「AI 数字分身（Digital Twin）」作品集。
候选人把个人信息 / 简历 / 项目 / 博客结构化后，由 AI 替代他和面试官对话。

## 为什么要做这个
- 节约双方时间：AI 先回答高频问题，面试官时间留给深度考察
- 项目本身就是简历：用作品集证明工程能力（meta portfolio）
- 差异化：从千篇一律的简历 PDF 中脱颖而出

## 技术架构
- 后端：FastAPI + LangGraph + LangChain
- LLM：MiniMax abab（对话）+ MiniMax abab5.5（意图分类）+ BGE-Reranker-v2-m3（重排）
- Embedding：MiniMax embo-01
- 向量库：Milvus Lite（嵌入式，无需 Docker）
- 前端：纯静态 HTML + TailwindCSS（CDN），可托管在 Vercel
- 追踪：LangSmith
- 评估：RAGAS（6 项指标）

## 关键设计
- 5 类意图路由（Tool Calling）
- 3 路并发混合检索（向量 + BM25 + 关键词衍生）
- ⟪n⟫ 引用标注（每个事实可回溯）
- 流式 SSE 输出（首 token < 1s）
- 三级失败回退（Rerank → 检索 → 兜底）
- 多轮对话记忆
- Milvus Lite 嵌入式：零运维，单进程部署

## 部署方式
- 单机：python main.py（端口 8000）+ python -m http.server（前端端口 5500）
- 容器：docker compose up（一键启动 API + 前端）
- 托管前端：Vercel / GitHub Pages / Nginx

## 设计哲学
「项目本身就是最好的简历」—— 候选人做的这个项目在展示他的工程能力。
"""