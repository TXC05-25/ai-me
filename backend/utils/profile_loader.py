"""
加载候选人结构化信息（YAML + Markdown + JSONL）
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from config import DATA_DIR, PROJECTS_DIR
from utils.logger import logger


def load_profile() -> dict:
    """加载 profile.yaml（候选人结构化信息）"""
    profile_path = DATA_DIR / "profile.yaml"
    if not profile_path.exists():
        logger.warning(f"profile.yaml 不存在：{profile_path}")
        return {"name": "谭修诚", "title": "AI 应用开发工程师（Python 方向）"}

    with open(profile_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_resume_markdown() -> str:
    """加载 resume.md（简历全文，最权威来源）"""
    resume_path = DATA_DIR / "resume.md"
    if not resume_path.exists():
        logger.warning(f"resume.md 不存在：{resume_path}")
        return ""
    return resume_path.read_text(encoding="utf-8")


def load_projects() -> list[dict]:
    """扫描 projects/ 目录，返回项目卡片信息列表"""
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for md_path in sorted(PROJECTS_DIR.glob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
            # 从 frontmatter 解析元数据（如果有）
            meta = {}
            content = text
            if text.startswith("---"):
                try:
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        meta = yaml.safe_load(parts[1]) or {}
                        content = parts[2].strip()
                except Exception:
                    pass

            # 第一段作为摘要
            lines = content.split("\n")
            summary = ""
            for line in lines:
                if line.strip() and not line.startswith("#"):
                    summary = line.strip()[:200]
                    break

            projects.append({
                "id": md_path.stem,
                "name": meta.get("name", md_path.stem),
                "summary": summary,
                "tech_stack": meta.get("tech_stack", []),
                "repo": meta.get("repo", ""),
                "demo": meta.get("demo", ""),
                "highlights": meta.get("highlights", []),
                "tags": meta.get("tags", []),
                "file": str(md_path.relative_to(DATA_DIR.parent)),
            })
        except Exception as e:
            logger.warning(f"解析项目失败：{md_path.name}: {e}")
    return projects


def load_qa_pairs() -> list[dict]:
    """加载 qa_pairs.jsonl（高频问答对）"""
    qa_path = DATA_DIR / "qa_pairs.jsonl"
    if not qa_path.exists():
        return []
    pairs = []
    with open(qa_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                pairs.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning(f"qa_pairs.jsonl 解析失败：{line[:50]}")
    return pairs