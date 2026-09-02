"""
LangSmith 全链路追踪初始化
"""

from __future__ import annotations

import os

from utils.logger import logger


def init_langsmith():
    """初始化 LangSmith 追踪"""
    if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true":
        api_key = os.getenv("LANGCHAIN_API_KEY")
        if not api_key:
            logger.warning("LANGCHAIN_TRACING_V2=true 但 LANGCHAIN_API_KEY 未配置，跳过")
            return
        logger.info(f"✅ LangSmith 追踪已启用 | project={os.getenv('LANGCHAIN_PROJECT', 'ai-me')}")
    else:
        logger.info("LangSmith 追踪未启用（如需开启请配置 .env 中的 LANGCHAIN_* 变量）")