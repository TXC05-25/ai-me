"""
3 路并发混合检索（ChromaDB + BM25 + 关键词衍生）
====================================================
"""

from __future__ import annotations

import asyncio
import re
from typing import Optional

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from config import CHROMA_DB_PATH, CHROMA_COLLECTION
from utils.logger import logger

_client = None
_bm25 = None
_bm25_docs: list[Document] = []


def _get_client():
    """懒加载 ChromaDB 客户端"""
    global _client
    if _client is None:
        import chromadb
        from chromadb.config import Settings
        from pathlib import Path
        Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def _get_bm25():
    """从 ChromaDB 拉取所有文档，构建 BM25 索引（懒加载）"""
    global _bm25, _bm25_docs
    if _bm25 is not None:
        return _bm25
    client = _get_client()
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"},
    )
    # BM25 索引所有文档（不再限制 qa_role）
    rows = collection.get(include=["documents", "metadatas"])
    _bm25_docs = [
        Document(page_content=r, metadata=m or {})
        for r, m in zip(rows["documents"] or [], rows["metadatas"] or [])
    ]
    if not _bm25_docs:
        logger.warning("BM25 索引：ChromaDB 中无文档")
        return None
    _bm25 = BM25Retriever.from_documents(_bm25_docs)
    return _bm25


def _embed_query(query: str) -> list[float]:
    """MiniMax Embedding 查询（type=query）"""
    import httpx
    from config import EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL
    resp = httpx.post(
        f"{EMBEDDING_BASE_URL.rstrip('/')}/embeddings",
        headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}", "Content-Type": "application/json"},
        json={"model": EMBEDDING_MODEL, "texts": [query], "type": "query"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    vectors = data.get("vectors") or []
    if not vectors or vectors[0] is None:
        raise ValueError(f"No embedding data: {data}")
    return vectors[0]


def _build_where(doc_filter: Optional[dict]) -> Optional[dict]:
    """合并 doc_filter 过滤

    ChromaDB 规则：
    - 单字段用单值：{"source_dir": "projects"}
    - 多字段用 $and：{"$and": [...]}

    注意：不再强制加 qa_role=answer 过滤，避免漏掉非 qa_pairs 的文档
    （profile.yaml / resume.md / projects / blogs 等用 source_dir 区分）
    """
    if not doc_filter:
        return None
    if len(doc_filter) == 1:
        return doc_filter
    return {"$and": [{k: {"$eq": v}} for k, v in doc_filter.items()]}


async def hybrid_retrieve(
    query: str,
    top_k: int = 10,
    doc_filter: Optional[dict] = None,
) -> list[dict]:
    """3 路并发：ChromaDB 向量 + BM25 + 关键词衍生"""
    client = _get_client()

    async def vector_search():
        try:
            collection = client.get_or_create_collection(
                name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"},
            )
            vector = _embed_query(query)
            where = _build_where(doc_filter)
            results = await asyncio.to_thread(
                collection.query,
                query_embeddings=[vector],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            items = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    items.append({
                        "block_id": meta.get("block_id", doc_id),
                        "doc_id": meta.get("doc_id", ""),
                        "source": meta.get("source", ""),
                        "source_dir": meta.get("source_dir", ""),
                        "title": meta.get("title", ""),
                        "text": results["documents"][0][i],
                        "score": 1 - results["distances"][0][i],
                    })
            return items
        except Exception as e:
            logger.warning(f"[VECTOR] 检索失败: {e}")
            return []

    async def bm25_search():
        try:
            bm25 = _get_bm25()
            if not bm25:
                return []
            docs = await asyncio.to_thread(bm25.invoke, query)
            return [
                {**d.metadata, "text": d.page_content, "score": 0.8}
                for d in docs[:top_k]
            ]
        except Exception as e:
            logger.warning(f"[BM25] 检索失败: {e}")
            return []

    async def keyword_search():
        try:
            kws = _extract_keywords(query)
            if not kws:
                return []
            vector = _embed_query(" ".join(kws))
            collection = client.get_or_create_collection(
                name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"},
            )
            where = _build_where(doc_filter)
            results = await asyncio.to_thread(
                collection.query,
                query_embeddings=[vector],
                n_results=top_k // 2,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            items = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    items.append({
                        "block_id": meta.get("block_id", doc_id),
                        "doc_id": meta.get("doc_id", ""),
                        "source": meta.get("source", ""),
                        "source_dir": meta.get("source_dir", ""),
                        "title": meta.get("title", ""),
                        "text": results["documents"][0][i],
                        "score": 0.6,
                    })
            return items
        except Exception as e:
            logger.warning(f"[KEYWORD] 检索失败: {e}")
            return []

    vector_res, bm25_res, kw_res = await asyncio.gather(
        vector_search(), bm25_search(), keyword_search()
    )

    # 去重合并
    seen, merged = set(), []
    for lst in [vector_res, bm25_res, kw_res]:
        for item in lst:
            bid = item.get("block_id")
            if bid and bid not in seen:
                seen.add(bid)
                merged.append(item)

    logger.debug(f"[RETRIEVE] vector={len(vector_res)} bm25={len(bm25_res)} kw={len(kw_res)} merged={len(merged)}")
    return merged[:top_k]


def _extract_keywords(query: str) -> list[str]:
    """jieba 提取实体词"""
    try:
        import jieba.posseg as pseg
        return [w for w, f in pseg.cut(query) if len(w) >= 2 and f.startswith(("n", "vn", "eng"))][:5]
    except Exception:
        return [t for t in re.split(r"[\s,，。！？?]+", query) if 2 <= len(t) <= 10][:5]