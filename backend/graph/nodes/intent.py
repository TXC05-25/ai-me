"""
意图分类节点（改进版）
========================
简化版：不用 Tool Calling，直接用普通 LLM 调用生成 JSON
更可靠：失败时回退用原始问题做检索，不影响主流程
"""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from config import INTENT_MODEL
from utils.common import llm
from utils.metrics import StageTimer
from utils.retry import retry_with_backoff
from utils.logger import node_logger

log = node_logger

# 5 类意图 + 1 类隐私拒答
VALID_INTENTS = {"profile_qa", "project_detail", "skill_assessment", "small_talk", "meta_question", "refused"}

# 隐私/情感话题关键词 → 命中后直接拒绝回答
REFUSE_KEYWORDS = [
    "女朋友", "男友", "男朋友", "女友", "老婆", "老公", "媳妇",
    "恋爱", "谈恋爱", "相亲", "对象", "暗恋", "喜欢谁",
    "有没有对象", "有对象吗", "有女朋友", "有男朋友",
    "有对象", "感情", "单身", "已婚", "未婚", "结婚", "离婚",
    "前任", "分手", "出轨", "劈腿",
]

# 关键词启发（兜底，LLM 不可用时使用）
# 注意：顺序很重要！meta_question 关键词要更具体
INTENT_KEYWORDS = {
    "meta_question": ["ai-me", "这个ai", "这个项目用", "这个项目怎么", "技术栈", "怎么部署", "架构", "设计哲学"],
    "project_detail": ["做过", "做过什么", "最复杂", "最有挑战", "最难", "详细介绍", "langgraph", "rag 客服", "哪个项目"],
    "skill_assessment": ["原理", "怎么实现", "为什么", "什么是", "解释", "pagedattention", "flashattention", "agent", "tool calling", "如何选择", "区别"],
    "small_talk": ["你好", "hi", "hello", "嗨", "在吗", "干嘛", "谢谢", "再见"],
}


@retry_with_backoff(max_attempts=2)
async def intent_node(state: dict) -> dict:
    from utils.metrics import new_sample
    sample = state.get("_timing_sample") or new_sample()
    state["_timing_sample"] = sample

    question = state.get("question", "")

    with StageTimer(sample, "intent"):
        # 0. 隐私/情感话题拦截 → 直接拒答（不检索、不调 LLM）
        if _is_refused_question(question):
            log.info(f"[INTENT-REFUSE] {question[:30]} -> refused")
            return {
                "intent": "refused",
                "thinking": "(隐私话题，拒答)",
                "routed_query": question,
            }

        # 1. 先用关键词启发（兜底，毫秒级）
        keyword_intent = _keyword_intent(question)

        # 2. 再用 LLM 分类（更准确但可能失败）
        try:
            chat = llm(model=INTENT_MODEL, temperature=0.0)
            sys_prompt = (
                "你是意图分类器。根据用户问题，输出 JSON 格式："
                '{"intent": "profile_qa|project_detail|skill_assessment|small_talk|meta_question", "thinking": "简短理由"}'
            )
            user_prompt = (
                f"问题：{question}\n\n"
                "5 类意图说明：\n"
                "- profile_qa: 关于候选人个人信息（教育/背景/实习/优缺点等）\n"
                "- project_detail: 关于项目细节（具体技术/实现/难点/方案）\n"
                "- skill_assessment: 关于技术原理（解释概念/对比方案）\n"
                "- small_talk: 闲聊寒暄\n"
                "- meta_question: 关于 AI-Me 项目本身（架构/技术栈/部署）\n\n"
                "只输出 JSON，不要其他内容。"
            )
            response = await chat.ainvoke([
                SystemMessage(content=sys_prompt),
                HumanMessage(content=user_prompt),
            ])
            content = response.content.strip()
            # 提取 JSON
            m = re.search(r'\{[^{}]*"intent"[^{}]*\}', content, re.DOTALL)
            if m:
                parsed = json.loads(m.group())
                llm_intent = parsed.get("intent", "").strip().lower()
                if llm_intent in VALID_INTENTS:
                    log.info(f"[INTENT-LLM] {question[:30]} -> {llm_intent}")
                    return {
                        "intent": llm_intent,
                        "thinking": parsed.get("thinking", ""),
                        "routed_query": question,  # 用原问题检索，避免乱码
                    }
        except Exception as e:
            log.warning(f"[INTENT-LLM] 失败: {e}")

        # 3. LLM 失败，用关键词
        log.info(f"[INTENT-KEYWORD] {question[:30]} -> {keyword_intent}")
        return {
            "intent": keyword_intent,
            "thinking": "(关键词启发)",
            "routed_query": question,  # 用原问题
        }


def _keyword_intent(question: str) -> str:
    """基于关键词的兜底意图分类（按优先级匹配）"""
    q = question.lower()
    # 按优先级遍历（meta > project > skill > smalltalk > profile）
    for intent in ["meta_question", "project_detail", "skill_assessment", "small_talk"]:
        keywords = INTENT_KEYWORDS.get(intent, [])
        for kw in keywords:
            if kw in q:
                return intent
    return "profile_qa"  # 默认


def _is_refused_question(question: str) -> bool:
    """检测是否属于隐私/情感话题（女友、恋爱、感情等）"""
    if not question:
        return False
    q = question.lower()
    for kw in REFUSE_KEYWORDS:
        if kw in q:
            return True
    return False