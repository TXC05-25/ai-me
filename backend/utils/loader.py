"""
文档加载 + ChromaDB 向量化
==============================
ChromaDB 优势：
- 纯 Python，零 native 依赖
- 自动持久化到文件夹
- API 简单，LangChain 集成好
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.config import Settings
import httpx

from config import (
    DATA_DIR, PROJECTS_DIR, BLOGS_DIR,
    CHROMA_DB_PATH, CHROMA_COLLECTION,
    EMBEDDING_DIM, EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL,
)
from utils.chunker import chunk_markdown, chunk_jsonl, generate_doc_id
from utils.profile_loader import load_profile, load_resume_markdown, load_qa_pairs
from utils.logger import logger

_client_cache = {}


def _get_client() -> chromadb.PersistentClient:
    """懒加载 ChromaDB 客户端（单例）"""
    if "client" not in _client_cache:
        Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
        _client_cache["client"] = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
    return _client_cache["client"]


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """调用 MiniMax Embedding API

    MiniMax 与 OpenAI 差异:
    - 参数名是 `texts`（不是 `input`）
    - 需要 `type` 参数（`db` 用于入库，`query` 用于查询）
    """
    url = f"{EMBEDDING_BASE_URL.rstrip('/')}/embeddings"
    try:
        resp = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {EMBEDDING_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": EMBEDDING_MODEL, "texts": texts, "type": "db"},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        vectors = data.get("vectors") or []
        if not vectors or vectors[0] is None:
            raise ValueError(f"No embedding data received: {data}")
        return vectors
    except Exception as e:
        logger.error(f"Embedding API 调用失败: {e}")
        raise


def _ensure_collection():
    """确保 collection 存在"""
    client = _get_client()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def build_knowledge_base(force_rebuild: bool = False) -> chromadb.Collection:
    """构建知识库：扫描资料 → 分块 → 向量化 → 写入 ChromaDB"""
    client = _get_client()

    if force_rebuild:
        try:
            client.delete_collection(CHROMA_COLLECTION)
            logger.info("已删除旧 collection")
        except Exception:
            pass

    collection = _ensure_collection()
    blocks = load_all_blocks()
    if not blocks:
        logger.warning("未加载到任何文档")
        return collection

    logger.info(f"共 {len(blocks)} 个 Block，开始向量化...")

    batch = 32  # MiniMax 单次最多 ~64 条文本
    existing_ids = set(collection.get()["ids"])

    for i in range(0, len(blocks), batch):
        chunk = blocks[i:i + batch]
        new_blocks = [b for b in chunk if b["block_id"] not in existing_ids]
        if not new_blocks:
            continue
        logger.info(f"  向量化 {len(new_blocks)} 个 block（{i+1}-{i+len(new_blocks)}/{len(blocks)}）...")
        vectors = _embed_batch([b["text"] for b in new_blocks])
        collection.add(
            ids=[b["block_id"] for b in new_blocks],
            embeddings=vectors,
            documents=[b["text"][:8000] for b in new_blocks],
            metadatas=[
                {
                    "block_id": b["block_id"],
                    "source": b["source"],
                    "source_dir": b.get("source_dir", "root"),
                    "doc_id": b["doc_id"],
                    "title": b.get("title", "")[:256],
                    "qa_role": b.get("qa_role", ""),  # qa_pairs 的 q/answer 标记
                }
                for b in new_blocks
            ],
        )

    logger.info(f"✅ ChromaDB 构建完成，共 {len(blocks)} 个 Block")
    return collection


def load_all_blocks() -> list[dict]:
    """扫描所有来源，返回 Block 列表"""
    blocks = []

    profile = load_profile()
    if profile:
        text = yaml_to_markdown(profile)
        if text.strip():
            blocks.extend(chunk_markdown(text, generate_doc_id(DATA_DIR / "profile.yaml"), "profile.yaml"))

    resume = load_resume_markdown()
    if resume.strip():
        blocks.extend(chunk_markdown(resume, generate_doc_id(DATA_DIR / "resume.md"), "resume.md"))

    if PROJECTS_DIR.exists():
        for md in sorted(PROJECTS_DIR.glob("*.md")):
            text = md.read_text(encoding="utf-8").strip()
            if text:
                blocks.extend(chunk_markdown(text, generate_doc_id(md), f"projects/{md.name}"))

    if BLOGS_DIR.exists():
        for md in sorted(BLOGS_DIR.glob("*.md")):
            text = md.read_text(encoding="utf-8").strip()
            if text:
                blocks.extend(chunk_markdown(text, generate_doc_id(md), f"blogs/{md.name}"))

    qa = load_qa_pairs()
    if qa:
        blocks.extend(chunk_jsonl(qa, "qa_pairs.jsonl"))

    from graph.meta import META_DOC
    if META_DOC.strip():
        blocks.extend(chunk_markdown(META_DOC, "meta-doc", "meta/PROJECT.md"))

    logger.info(f"加载 {len(blocks)} 个 Block（profile/resume/projects/blogs/qa_pairs/meta）")
    return blocks


def yaml_to_markdown(profile: dict) -> str:
    """profile.yaml → Markdown 文本"""
    lines = ["# 候选人基本信息\n"]
    for key, value in profile.items():
        if isinstance(value, dict):
            lines.append(f"\n## {_format_key(key)}\n")
            lines.extend(
                f"- **{_format_key(k)}**: {', '.join(map(str, v)) if isinstance(v, list) else v}"
                for k, v in value.items()
            )
        elif isinstance(value, list):
            lines.append(f"\n## {_format_key(key)}\n")
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        lines.append(f"- **{_format_key(k)}**: {v}")
                else:
                    lines.append(f"- {item}")
        else:
            lines.append(f"- **{_format_key(key)}**: {value}")
    return "\n".join(lines)


def _format_key(key: str) -> str:
    return {
        "name": "姓名", "title": "求职意向", "email": "邮箱", "phone": "电话",
        "github": "GitHub", "linkedin": "LinkedIn", "education": "教育背景",
        "experience": "工作经历", "projects": "项目经历", "skills": "技能栈",
        "awards": "荣誉奖项", "languages": "语言能力",
    }.get(key, key.replace("_", " ").title())


if __name__ == "__main__":
    build_knowledge_base(force_rebuild=True)