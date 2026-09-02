"""
Pydantic 数据模型（请求 / 响应 Schema）
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from config import MAX_INPUT_LENGTH


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    stream: bool = False

    @field_validator("question")
    @classmethod
    def check_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("问题不能为空")
        if len(v) > MAX_INPUT_LENGTH:
            raise ValueError(f"问题长度超过 {MAX_INPUT_LENGTH} 字符上限")
        return v


class RecommendRequest(BaseModel):
    """根据当前会话上下文推荐下一个面试问题"""
    session_id: str
    jd_text: Optional[str] = Field(None, description="可选：岗位 JD，用于定制问题")


class ExportRequest(BaseModel):
    session_id: str
    format: str = Field("markdown", pattern="^(markdown|json)$")


class Citation(BaseModel):
    index: int
    block_id: str
    doc_id: str
    source: str
    snippet: str
    source_dir: Optional[str] = None


class RecommendedQuestion(BaseModel):
    question: str
    intent: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    intent: Optional[str] = None
    citations: list[Citation] = []
    recommended_questions: list[RecommendedQuestion] = []