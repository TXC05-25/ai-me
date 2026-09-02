"""
工具函数：格式化引用、解析推荐问题等
"""

from __future__ import annotations

import re


def format_citations(blocks: list[dict]) -> list[dict]:
    """把 reranked blocks 格式化为 citations"""
    citations = []
    for i, block in enumerate(blocks, start=1):
        citations.append({
            "index": i,
            "block_id": block.get("block_id"),
            "doc_id": block.get("doc_id"),
            "source": block.get("source"),
            "snippet": block.get("text", "")[:200] + ("..." if len(block.get("text", "")) > 200 else ""),
            "source_dir": block.get("source_dir"),
        })
    return citations


def build_recommend_questions(text: str) -> list[dict]:
    """解析 LLM 输出的推荐问题文本

    输入示例：
        1. 你在 RAG 项目中如何处理检索召回率低的问题？ —— 考察向量检索调优经验
        2. ...
    """
    questions = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # 去掉编号
        line = re.sub(r"^\d+[\.、]\s*", "", line)
        # 拆分「问题 —— 意图」
        if "——" in line:
            q, intent = line.split("——", 1)
            questions.append({"question": q.strip(), "intent": intent.strip()})
        elif "—" in line:
            q, intent = line.split("—", 1)
            questions.append({"question": q.strip(), "intent": intent.strip()})
        else:
            questions.append({"question": line, "intent": "未指定"})

        if len(questions) >= 5:
            break
    return questions