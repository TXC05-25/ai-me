"""
响应节点
=========
- generate_node   答案生成（带引用 + 推荐追问）
- chat_node       闲聊直答
- meta_node       回答关于项目本身的问题
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from config import SYSTEM_PROMPT_TEMPLATE, TEMPERATURE
from graph.tools import format_citations
from utils.common import llm, format_history
from utils.metrics import StageTimer
from utils.retry import retry_with_backoff
from utils.logger import node_logger

log = node_logger


@retry_with_backoff(max_attempts=3)
async def generate_node(state: dict) -> dict:
    """基于上下文 + 历史生成答案（带降级策略）"""
    from utils.metrics import new_sample
    question = state.get("question", "")
    context = state.get("context", "")
    history_str = format_history(state.get("history", []))
    intent = state.get("intent", "profile_qa")
    sample = state.get("_timing_sample") or new_sample()

    # 调试：打印 state 关键字段
    log.info(f"[GENERATE-DEBUG] question={question!r}, intent={intent!r}, context_len={len(context)}")

    # === 降级策略 ===
    # 判断 1：top 检索分数低 → 降级到"轻松闲聊"风格
    reranked = state.get("reranked_blocks", []) or []
    top_score = max((b.get("score", 0) for b in reranked), default=0)

    # 判断 2：问题太短 / 模糊 → 降级
    is_short_question = len(question.strip()) < 5

    # 判断 3：context 为空 → 降级
    empty_context = len(context.strip()) < 50

    # 综合判断：满足任一条件就降级
    degraded = top_score < 0.4 or is_short_question or empty_context

    # 极低置信兜底：top_score 太低（< 0.15）且用户问的是项目/技能类问题时，
    # 直接说「知识库没这条」而不是让 LLM 瞎编，避免幻觉
    no_match_no_hallucinate = (
        top_score < 0.15
        and intent in {"project_detail", "skill_assessment"}
        and not is_short_question
        and not empty_context
    )
    if no_match_no_hallucinate:
        log.info(f"[GENERATE] 知识库无命中 (top_score={top_score:.2f}, intent={intent})，直接兜底")
        answer = (
            "这个问题我知识库里暂时没有详细的资料 😅\n"
            "你可以换个方向问，比如：\n"
            "• 我最近在做哪个项目？\n"
            "• RAG / LangGraph 的实现细节\n"
            "• 我的技术栈和实习经历"
        )
        sample.token_count = len(answer)
        log.info(f"[GENERATE] 兜底 answer_len={len(answer)} citations=0")
        recommendations = await _gen_recommendations(history_str, question, answer)
        return {
            "answer": answer,
            "citations": [],
            "recommended_questions": recommendations,
            "final_answer": {
                "answer": answer,
                "citations": [],
                "recommended_questions": recommendations,
                "intent": intent,
            },
        }

    if degraded:
        log.info(f"[GENERATE] 降级模式: top_score={top_score:.2f}, short={is_short_question}, empty_ctx={empty_context}")
        # 降级 prompt：基于简历 + 轻松风格
        system_prompt = _build_degraded_prompt(question, history_str, intent)
    else:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            context=context, history=history_str, question=question,
        )

    # small_talk 仍然走闲聊 prompt
    if intent == "small_talk" and not context:
        system_prompt = (
            "你是 AI-Me —— 候选人 谭修诚 的 AI 数字分身。"
            "大模型算法/工程方向，热爱开源。请友好自然地闲聊，1-3 句话即可。"
        )

    with StageTimer(sample, "generate"):
        chat = llm(temperature=TEMPERATURE)
        answer = (await chat.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ])).content.strip()

        recommendations = await _gen_recommendations(history_str, question, answer)
        citations = format_citations(state.get("reranked_blocks", []))

    sample.token_count = len(answer)

    log.info("[GENERATE] answer_len=" + str(len(answer)) + " citations=" + str(len(citations)))

    return {
        "answer": answer,
        "citations": citations,
        "recommended_questions": recommendations,
        "final_answer": {
            "answer": answer,
            "citations": citations,
            "recommended_questions": recommendations,
            "intent": intent,
        },
    }


def _build_degraded_prompt(question: str, history_str: str, intent: str) -> str:
    """降级 prompt：当 LLM 不确定时使用，让它轻松回答"""
    return f"""你是谭修诚，正在和面试官轻松交流。基于你的真实经历回答问题。

【你的核心信息】
- 武汉华夏理工学院 2027 届本科应届毕业生（电子信息工程）
- 杭州亿渡网络科技有限公司 AI 应用开发实习生
- 独立完成 RAG 客服问答系统（LangGraph 版，准确率提升 35%）
- 正在做 AI-Me 项目（AI 数字分身作品集）

【对话历史】
{history_str}

【面试官问题】
{question}

【回答规则】
- 第一人称，语气自然
- 基于你的真实经历和简历
- 不知道就说不知道，不要瞎编
- 不要说"问题乱码"、"我看不懂"、"我无法回答"
- 不要复述问题
- 2-4 句话

我的回答："""


async def _gen_recommendations(history_str: str, question: str, answer: str) -> list[dict]:
    """基于对话上下文生成 2 个推荐追问"""
    try:
        chat = llm(temperature=0.5)
        prompt = (
            "基于以下对话，给面试官推荐 2 个值得深入追问的问题。\n"
            "只输出问题列表，每行一个，不要编号，不要其他解释。\n\n"
            "【对话历史】\n" + history_str + "\n\n"
            "【最近问题】" + question + "\n"
            "【最近回答】" + answer[:500] + "\n\n"
            "【推荐问题】"
        )
        content = (await chat.ainvoke([HumanMessage(content=prompt)])).content.strip()
        recs = []
        for line in content.split("\n"):
            line = line.strip().lstrip("0123456789.、 ")
            if 5 < len(line) < 100:
                recs.append({"question": line, "intent": "auto"})
            if len(recs) >= 2:
                break
        return recs
    except Exception:
        return []


async def chat_node(state: dict) -> dict:
    """闲聊模式：直接 LLM 对答"""
    return await generate_node(state)


async def refuse_node(state: dict) -> dict:
    """隐私/情感话题：礼貌拒绝回答，不检索、不调 LLM"""
    question = state.get("question", "")
    log.info(f"[REFUSE] 已拦截敏感问题: {question[:30]}")
    answer = (
        "这个问题属于个人隐私，我不太方便聊 🙂\n"
        "我们还是回到技术、项目或者学习这些话题吧——"
        "比如你可以问我：\n"
        "• 你最近在做哪个项目？\n"
        "• RAG / LangGraph 的实现细节\n"
        "• 你的技术栈和实习经历"
    )
    return {
        "answer": answer,
        "citations": [],
        "recommended_questions": [
            {"question": "你最近在做哪个项目？", "intent": "project_detail"},
            {"question": "介绍一下 RAG 系统的实现细节", "intent": "skill_assessment"},
        ],
        "final_answer": {
            "answer": answer,
            "citations": [],
            "recommended_questions": [
                {"question": "你最近在做哪个项目？", "intent": "project_detail"},
                {"question": "介绍一下 RAG 系统的实现细节", "intent": "skill_assessment"},
            ],
            "intent": "refused",
        },
    }


@retry_with_backoff(max_attempts=2)
async def meta_node(state: dict) -> dict:
    """回答关于本项目架构 / 部署 / 设计哲学的问题"""
    from utils.metrics import new_sample
    question = state.get("question", "")
    context = state.get("context") or "（项目本身的相关文档未加载到知识库）"
    sample = state.get("_timing_sample") or new_sample()

    with StageTimer(sample, "generate"):
        system_prompt = (
            "你是「AI-Me」元信息助手。面试官想了解这个项目本身（不是候选人）。\n\n"
            "【项目背景】\n"
            "AI-Me 是一个面向面试官的「AI 数字分身」作品集，基于 RAG + LangGraph 构建。\n"
            "技术栈：FastAPI + LangGraph + LangChain + Milvus Lite + MiniMax abab + BGE-Reranker。\n"
            "前端：纯静态 HTML + TailwindCSS（CDN），可托管在 Vercel。\n"
            "设计哲学：项目本身就是最好的简历。\n\n"
            "【相关上下文】\n" + context + "\n\n"
            "请基于以上信息回答面试官关于项目架构 / 部署 / 技术选型 / 设计哲学的问题。"
        )

        chat = llm(temperature=0.2)
        try:
            answer = (await chat.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=question),
            ])).content.strip()
            return {
                "answer": answer,
                "citations": format_citations(state.get("reranked_blocks", [])),
                "final_answer": {"answer": answer},
            }
        except Exception as e:
            log.exception("[META] failed")
            return {"answer": "这个问题我暂时答不上来 😅"}