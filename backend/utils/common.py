"""
共享工具：LLM 客户端构造、对话历史格式化
==========================================
所有节点共享，避免重复代码
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_FALLBACK_API_KEY,
    LLM_FALLBACK_BASE_URL,
    LLM_FALLBACK_MODEL,
    TEMPERATURE,
)
from utils.logger import logger


def llm(model: str | None = None, temperature: float = TEMPERATURE) -> ChatOpenAI:
    """构造主 LLM 客户端（Qwen / 其他）"""
    return ChatOpenAI(
        model=model or LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=temperature,
    )


def fallback_llm(model: str | None = None, temperature: float = TEMPERATURE) -> ChatOpenAI:
    """构造备用 LLM 客户端（默认 DeepSeek）"""
    return ChatOpenAI(
        model=model or LLM_FALLBACK_MODEL,
        api_key=LLM_FALLBACK_API_KEY,
        base_url=LLM_FALLBACK_BASE_URL,
        temperature=temperature,
    )


def _is_retryable_llm_error(e: Exception) -> bool:
    """判断是否触发备用模型切换：连接错误 / 超时 / 5xx / 鉴权失败"""
    name = type(e).__name__
    msg = str(e).lower()
    # 连接/超时类
    if name in {"OpenAIConnectionError", "APITimeoutError", "Timeout", "ConnectionError"}:
        return True
    if "connection error" in msg or "timeout" in msg or "timed out" in msg:
        return True
    # 服务端 5xx
    if "500" in msg or "502" in msg or "503" in msg or "504" in msg or "529" in msg:
        return True
    # 鉴权/配额（主模型不可用，走备用）
    if name in {"AuthenticationError", "PermissionDeniedError", "RateLimitError"}:
        return True
    if "401" in msg or "403" in msg or "429" in msg:
        return True
    if "invalid api key" in msg or "authentication" in msg or "rate limit" in msg or "quota" in msg:
        return True
    return False


async def ainvoke_with_fallback(chat, fallback_chat, payload, *, stage: str = "llm"):
    """调用主 LLM；连接/超时错误自动切到备用 LLM 重试 1 次。

    用法：
        chat = llm()
        fb    = fallback_llm()
        resp  = await ainvoke_with_fallback(chat, fb, [SystemMessage(...), HumanMessage(...)],
                                            stage="generate")
    """
    try:
        return await chat.ainvoke(payload)
    except Exception as e:
        if not _is_retryable_llm_error(e):
            raise
        logger.warning(
            f"[{stage}] 主模型失败（{type(e).__name__}: {str(e)[:120]}），切换备用模型 {LLM_FALLBACK_MODEL}"
        )
        try:
            return await fallback_chat.ainvoke(payload)
        except Exception as e2:
            logger.error(f"[{stage}] 备用模型也失败：{type(e2).__name__}: {str(e2)[:120]}")
            raise


def format_history(history: list[dict], max_turns: int = 6) -> str:
    """把对话历史格式化为文本，便于 Prompt 引用"""
    if not history:
        return "（无历史对话）"
    lines = [
        f"{'面试官' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in history[-max_turns * 2:]
    ]
    return "\n".join(lines)