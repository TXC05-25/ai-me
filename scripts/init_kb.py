"""
重建知识库（向量化）
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from utils.loader import build_knowledge_base
from utils.logger import logger


if __name__ == "__main__":
    logger.info("开始重建知识库...")
    build_knowledge_base(force_rebuild=True)
    logger.info("✅ 知识库重建完成")