"""
LangGraph 图结构（改进版）
===========================
流程：
  START → intent → (chat | recommend | rewrite)
    → rewrite → retrieve → rerank → assemble_context
    → generate → END

改进：
- meta_question 不再跳过 retrieve，避免答非所问
- 所有非闲聊问题都走检索链
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from graph.nodes import (
    intent_node, rewrite_node, retrieve_node, rerank_node,
    assemble_context_node, generate_node, chat_node, meta_node, recommend_node,
)


def _route_by_intent(state: dict) -> str:
    """根据意图路由节点

    - recommend → recommend（推荐面试题）
    - 其他所有意图（包括 small_talk）→ rewrite（走检索链）
    """
    intent = state.get("intent", "profile_qa")
    if intent == "recommend":
        return "recommend"
    # small_talk 也走检索链：让 AI 至少能基于候选人信息回答"我是谁"
    return "rewrite"


def build_graph():
    """构建 LangGraph 状态图（懒加载）"""
    workflow = StateGraph(dict)

    # 注册节点
    for name, fn in [
        ("intent", intent_node),
        ("rewrite", rewrite_node),
        ("retrieve", retrieve_node),
        ("rerank", rerank_node),
        ("assemble_context", assemble_context_node),
        ("generate", generate_node),
        ("chat", chat_node),
        ("meta", meta_node),
        ("recommend", recommend_node),
    ]:
        workflow.add_node(name, fn)

    # 入口
    workflow.set_entry_point("intent")

    # 意图分流
    workflow.add_conditional_edges(
        "intent", _route_by_intent,
        {"chat": "chat", "recommend": "recommend", "rewrite": "rewrite"},
    )

    # 主干：检索链 → 生成
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "assemble_context")
    workflow.add_edge("assemble_context", "generate")

    # 收尾
    for node in ("generate", "chat", "meta", "recommend"):
        workflow.add_edge(node, END)

    return workflow.compile()


__all__ = ["build_graph"]