"""
共享工具：LLM 客户端构造、对话历史格式化
==========================================
所有节点共享，避免重复代码
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, TEMPERATURE


def llm(model: str | None = None, temperature: float = TEMPERATURE) -> ChatOpenAI:
    """构造 ChatOpenAI 客户端（MiniMax 兼容 OpenAI 协议）"""
    return ChatOpenAI(
        model=model or LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=temperature,
    )


def format_history(history: list[dict], max_turns: int = 6) -> str:
    """把对话历史格式化为文本，便于 Prompt 引用"""
    if not history:
        return "（无历史对话）"
    lines = [
        f"{'面试官' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in history[-max_turns * 2:]
    ]
    return "\n".join(lines)