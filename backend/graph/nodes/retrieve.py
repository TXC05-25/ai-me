"""
检索链节点
===========
- rewrite_node          问题改写（结合历史）
- retrieve_node         3 路并发混合检索
- rerank_node           重排
- assemble_context_node 组装上下文

每个节点均使用 StageTimer 计时，性能埋点到 state["timing"]
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from config import MAX_RETRIEVE_BLOCKS, RERANK_TOP_K
from utils.common import llm, format_history
from utils.metrics import StageTimer
from utils.retriever import hybrid_retrieve
from utils.rerank import rerank_blocks
from utils.retry import retry_with_backoff
from utils.logger import node_logger

log = node_logger


def _get_sample(state: dict):
    """从 state 拿到共享的 timing sample"""
    from utils.metrics import new_sample
    sample = state.get("_timing_sample")
    if sample is None:
        sample = new_sample()
        state["_timing_sample"] = sample
    return sample


@retry_with_backoff(max_attempts=2)
async def rewrite_node(state: dict) -> dict:
    """结合对话历史，将省略/指代问题改写为独立问句"""
    question = state.get("question", "")
    history_str = format_history(state.get("history", []))
    timing = _get_sample(state)

    with StageTimer(timing, "rewrite"):
        if not history_str.strip() or "（无" in history_str:
            return {"routed_query": question}

        chat = llm(temperature=0.0)
        prompt = (
            "结合对话历史，把下面这个可能含省略/指代的问题改写为独立问句。\n\n"
            "【对话历史】\n" + history_str + "\n\n"
            "【问题】" + question + "\n\n"
            "【改写后的独立问句】（只输出问句本身）"
        )

        try:
            rewritten = (await chat.ainvoke([HumanMessage(content=prompt)])).content.strip()
            if rewritten and len(rewritten) <= 200:
                log.info("[REWRITE] " + question[:30] + " -> " + rewritten[:30])
                return {"routed_query": rewritten}
        except Exception as e:
            log.warning("[REWRITE] failed, using original: " + str(e))

    return {"routed_query": question}


async def retrieve_node(state: dict) -> dict:
    """3 路并发混合检索（向量 + BM25 + 关键词衍生）"""
    # 优先用原问题（避免 routed_query 乱码），意图仅用于过滤文档来源
    question = state.get("question", "")
    query = state.get("routed_query") or question
    intent = state.get("intent", "profile_qa")
    log.info(f"[RETRIEVE-DEBUG] state.keys={list(state.keys())}, intent={intent!r}")

    # project_detail / skill_assessment / meta_question 走子集；其他走全集合
    if intent == "project_detail":
        doc_filter = {"source_dir": "projects"}
    elif intent == "skill_assessment":
        doc_filter = {"source_dir": "qa_pairs"}
    elif intent == "meta_question":
        doc_filter = {"source_dir": "meta"}
    else:
        doc_filter = None  # 全集合

    timing = _get_sample(state)

    with StageTimer(timing, "retrieve"):
        try:
            blocks = await hybrid_retrieve(query=query, top_k=MAX_RETRIEVE_BLOCKS, doc_filter=doc_filter)
            # 如果过滤后没结果，扩大到全集合
            if not blocks and doc_filter:
                log.info(f"[RETRIEVE] intent={intent} 过滤后无结果，扩大到全集合")
                blocks = await hybrid_retrieve(query=query, top_k=MAX_RETRIEVE_BLOCKS, doc_filter=None)
            log.info("[RETRIEVE] q=" + query[:30] + " -> " + str(len(blocks)) + " blocks (intent=" + intent + ")")
            return {"retrieved_blocks": blocks, "retrieved_count": len(blocks)}
        except Exception as e:
            log.exception("[RETRIEVE] failed, returning empty")
            return {"retrieved_blocks": [], "retrieved_count": 0, "error": str(e)}


async def rerank_node(state: dict) -> dict:
    """BGE-Reranker 重排（失败回退 hybrid top-k）"""
    blocks = state.get("retrieved_blocks", [])
    if not blocks:
        return {"reranked_blocks": [], "rerank": {"kept": 0, "model": "fallback"}}

    query = state.get("routed_query") or state.get("question", "")
    timing = _get_sample(state)

    with StageTimer(timing, "rerank"):
        try:
            ranked = await rerank_blocks(query=query, blocks=blocks, top_k=RERANK_TOP_K)
            log.info("[RERANK] kept " + str(len(ranked)) + "/" + str(len(blocks)))
            return {"reranked_blocks": ranked, "rerank": {"kept": len(ranked), "model": "rerank"}}
        except Exception as e:
            log.warning("[RERANK] failed, fallback top-" + str(RERANK_TOP_K) + ": " + str(e))
            return {
                "reranked_blocks": blocks[:RERANK_TOP_K],
                "rerank": {"kept": RERANK_TOP_K, "model": "fallback", "error": str(e)},
            }


async def assemble_context_node(state: dict) -> dict:
    """把 Rerank 后的 blocks 格式化为带 [n] 编号的上下文"""
    blocks = state.get("reranked_blocks", [])
    if not blocks:
        return {"context": "（知识库未命中相关内容）"}

    timing = _get_sample(state)
    with StageTimer(timing, "assemble"):
        parts = [
            "[" + str(i) + "] " + b["text"].strip() + "\n（来源: " + b.get("source", "?") + "）"
            for i, b in enumerate(blocks, 1)
        ]
        return {"context": "\n\n".join(parts)}