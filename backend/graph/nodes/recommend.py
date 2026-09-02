"""
推荐面试问题节点
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from config import RECOMMEND_QUESTION_PROMPT
from graph.tools import build_recommend_questions
from utils.common import llm, format_history
from utils.retry import retry_with_backoff
from utils.logger import node_logger

log = node_logger


@retry_with_backoff(max_attempts=2)
async def recommend_node(state: dict) -> dict:
    """根据历史 + JD 推荐面试问题"""
    history_str = format_history(state.get("history", []), max_turns=10)
    jd_text = state.get("jd_text", "（未提供 JD）")
    profile_summary = state.get("profile_summary", "候选人：谭修诚，大模型算法/工程方向")

    prompt = RECOMMEND_QUESTION_PROMPT.format(
        n=5, profile_summary=profile_summary, history=history_str, jd_text=jd_text,
    )

    chat = llm(temperature=0.7)
    try:
        content = (await chat.ainvoke([HumanMessage(content=prompt)])).content.strip()
        questions = build_recommend_questions(content)
        log.info("[RECOMMEND] generated " + str(len(questions)) + " questions")
        return {"recommended_questions": questions}
    except Exception as e:
        log.exception("[RECOMMEND] failed")
        return {"recommended_questions": []}