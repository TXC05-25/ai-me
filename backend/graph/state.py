"""
LangGraph 共享状态定义
"""

from __future__ import annotations

from typing import TypedDict, Optional
from utils.metrics import TimingSample


class RagState(TypedDict, total=False):
    """AI-Me 图状态（total=False 让所有字段可选，便于部分更新）"""

    # ===== 输入 =====
    question: str                          # 用户问题
    session_id: str                        # 会话 ID
    history: list[dict]                    # 对话历史
    mode: str                              # 模式：qa / recommend
    jd_text: Optional[str]                 # 可选 JD 文本

    # ===== 性能埋点 =====
    timing: TimingSample                   # 各节点耗时样本
    first_token_at: Optional[float]        # 首 token 时间戳

    # ===== 意图路由 =====
    intent: str                            # 意图分类
    thinking: str                          # LLM 思考过程
    routed_query: str                      # 路由后的问题（用于检索）

    # ===== 检索 =====
    retrieved_blocks: list[dict]           # 召回的 Block 列表
    retrieved_count: int                   # 召回数量
    reranked_blocks: list[dict]            # Rerank 后保留的 Block

    # ===== 生成 =====
    context: str                           # 组装好的知识库上下文（含 ⟪n⟫ 编号）
    answer: str                            # 最终答案
    final_answer: Optional[dict]           # 流式模式下的最终输出

    # ===== 引用 =====
    citations: list[dict]                  # 引用列表

    # ===== 推荐问题 =====
    recommended_questions: list[dict]      # 推荐面试题

    # ===== 元信息 =====
    error: Optional[str]                   # 错误信息