"""
Block 级文本分块器
===================
每个段落/章节切分为独立 Block，分配唯一 block_id（{doc_id}::{index:04d}）
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path


def chunk_markdown(text: str, doc_id: str, source: str) -> list[dict]:
    """把 Markdown 按二级标题切分为 Block

    每个 Block：
      {
        "block_id": "doc-abc::0001",
        "doc_id": "doc-abc",
        "source": "resume.md",
        "title": "教育背景",          # 当前 Block 的标题
        "text": "...",               # 内容
        "index": 1,
        "source_dir": "root",        # root / projects / blogs / qa_pairs / meta
      }
    """
    blocks = []

    # 按 ## 切分（保留原标题）
    sections = re.split(r"^(#{1,3})\s+(.+)$", text, flags=re.MULTILINE)

    # sections 结构：[前导内容, "#", "title1", "content1", "#", "title2", "content2", ...]
    if len(sections) < 3:
        # 没有标题，整个作为一块
        if text.strip():
            blocks.append({
                "block_id": f"{doc_id}::0000",
                "doc_id": doc_id,
                "source": source,
                "title": "",
                "text": text.strip(),
                "index": 0,
                "source_dir": _infer_source_dir(source),
            })
        return blocks

    # 处理第一段（前导内容）
    if sections[0].strip():
        blocks.append({
            "block_id": f"{doc_id}::0000",
            "doc_id": doc_id,
            "source": source,
            "title": "",
            "text": sections[0].strip(),
            "index": 0,
            "source_dir": _infer_source_dir(source),
        })

    idx = 1
    for i in range(1, len(sections), 3):
        if i + 2 >= len(sections):
            break
        title = sections[i + 1].strip()
        content = sections[i + 2].strip()
        if not content:
            continue
        blocks.append({
            "block_id": f"{doc_id}::{idx:04d}",
            "doc_id": doc_id,
            "source": source,
            "title": title,
            "text": f"## {title}\n\n{content}",
            "index": idx,
            "source_dir": _infer_source_dir(source),
        })
        idx += 1

    return blocks


def chunk_jsonl(qa_pairs: list[dict], source: str) -> list[dict]:
    """把 QA 对转换为 Block

    关键设计：每个 Q&A 存为 2 个 block：
    - block_a: 只有 Q（标题/检索用）
    - block_b: Q + A（答案）

    检索时，Q 命中 → 把对应的 Q+A 整体加入 context。
    这样能避免"问 FlashAttention 找到自我介绍"的问题。
    """
    blocks = []
    doc_id = "qa-pairs-" + str(uuid.uuid4())[:8]
    for i, qa in enumerate(qa_pairs):
        question = qa.get('question', '').strip()
        answer = qa.get('answer', '').strip()
        intent = qa.get('intent', '')

        # block 1: 问题（用于精确标题匹配）
        blocks.append({
            "block_id": f"{doc_id}::q{i:04d}",
            "doc_id": doc_id,
            "source": source,
            "title": question[:50],
            "text": f"## Q: {question}",
            "index": i * 2,
            "source_dir": "qa_pairs",
            "qa_index": i,
            "qa_role": "question",
        })

        # block 2: 完整 Q+A（用于语义检索）
        full_text = f"## Q: {question}\n\nA: {answer}"
        if intent:
            full_text += f"\n\n（分类：{intent}）"
        blocks.append({
            "block_id": f"{doc_id}::a{i:04d}",
            "doc_id": doc_id,
            "source": source,
            "title": question[:50],
            "text": full_text,
            "index": i * 2 + 1,
            "source_dir": "qa_pairs",
            "qa_index": i,
            "qa_role": "answer",
        })
    return blocks


def _infer_source_dir(source: str) -> str:
    """根据文件路径推断 source_dir"""
    if source.startswith("projects/"):
        return "projects"
    if source.startswith("blogs/"):
        return "blogs"
    if source.startswith("qa_pairs"):
        return "qa_pairs"
    if source.startswith("meta"):
        return "meta"
    return "root"


def generate_doc_id(file_path: Path) -> str:
    """从文件路径生成 doc_id"""
    return f"doc-{file_path.stem}-{str(uuid.uuid4())[:8]}"