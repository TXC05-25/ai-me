"""
BGE-Reranker 客户端
===================
调 SiliconFlow 的 BGE-Reranker-v2-m3
"""

from __future__ import annotations

import asyncio
import httpx

from config import RERANK_API_KEY, RERANK_BASE_URL, RERANK_MODEL
from utils.logger import logger


async def rerank_blocks(query: str, blocks: list[dict], top_k: int = 5) -> list[dict]:
    if not blocks:
        return []
    if not RERANK_API_KEY:
        logger.warning("RERANK_API_KEY 未配置，跳过 rerank")
        return blocks[:top_k]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{RERANK_BASE_URL}/rerank",
                headers={"Authorization": f"Bearer {RERANK_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": RERANK_MODEL, "query": query,
                    "documents": [b.get("text", "") for b in blocks],
                    "top_n": top_k, "return_documents": False,
                },
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])

        if not results:
            return blocks[:top_k]

        return [
            {**blocks[r["index"]], "rerank_score": r.get("relevance_score", 0)}
            for r in results
            if 0 <= r.get("index", -1) < len(blocks)
        ]
    except Exception as e:
        logger.warning(f"Rerank 失败：{e}，回退原始排序")
        return blocks[:top_k]