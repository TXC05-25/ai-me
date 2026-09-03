"""
全局配置（从 .env 读取）
==========================
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# ===== 服务配置 =====
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"

# ===== 数据目录 =====
DATA_DIR = ROOT_DIR / "backend" / "data"
PROJECTS_DIR = DATA_DIR / "projects"
BLOGS_DIR = DATA_DIR / "blogs"
VECTOR_DB_DIR = ROOT_DIR / "backend" / "vector_db"
LOGS_DIR = ROOT_DIR / "backend" / "logs"

for d in [VECTOR_DB_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ===== LLM =====
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# ===== Embedding =====
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.minimax.chat/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embo-01")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

# ===== 意图分类 =====
INTENT_MODEL = os.getenv("INTENT_MODEL", "abab5.5-chat")

# ===== 重排 =====
RERANK_API_KEY = os.getenv("RERANK_API_KEY", LLM_API_KEY)
RERANK_BASE_URL = os.getenv("RERANK_BASE_URL", "https://api.siliconflow.cn/v1")
RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")

# ===== ChromaDB =====
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(VECTOR_DB_DIR / "chroma"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "ai_me_kb")

# ===== LangSmith =====
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "ai-me")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

# ===== 应用行为 =====
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2000"))
MAX_RETRIEVE_BLOCKS = int(os.getenv("MAX_RETRIEVE_BLOCKS", "5"))
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "3"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
ENABLE_RECOMMEND_QUESTION = os.getenv("ENABLE_RECOMMEND_QUESTION", "true").lower() == "true"

# ===== 限流 =====
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "10"))

# ===== Prompt 模板（简化版，不强制引用，避免 LLM 拒答）=====
SYSTEM_PROMPT_TEMPLATE = """你是谭修诚，正在接受面试官的提问。

【你的核心简历信息】
- 学校：武汉华夏理工学院（民办本科，电子信息工程，2027 届本科应届毕业生）
- 实习公司：杭州亿渡网络科技有限公司（AI 应用开发实习生，2026.07 - 至今）
- 项目一：RAG 客服问答系统（LangGraph 版 · Block 级架构，准确率提升 35%）
- 项目二：AI-Me（当前项目，AI 数字分身作品集）
- 技术栈：LangGraph + LangChain + FastAPI + Python
- 荣誉：2024-2025 三好学生、校三等奖学金

【知识库上下文（可补充细节）】
{context}

【回答风格】
- 用第一人称（"我做过..."、"我的经验..."）
- 直接给答案，不解释
- 简洁具体
- 基于【核心简历信息】+【知识库上下文】回答

【特别注意】
- 不要说"问题显示乱码"、"我看不懂"、"我无法回答"等
- 不要解释问题为什么有问题
- 问题可能很短或口语化，直接基于【核心简历信息】回答即可

【回答示例】
问：你做过最复杂的项目是什么？
答：最复杂的是 RAG 客服问答系统（LangGraph 版 · Block 级架构），我主导了整个系统架构，实现了 35% 的准确率提升。

问：介绍一下你自己
答：我是 2027 届本科应届毕业生（武汉华夏理工学院 · 电子信息工程），目前在杭州亿渡网络科技有限公司实习做 AI 应用开发。

问：你好
答：你好！我是谭修诚，2027 届本科应届毕业生，目前在杭州亿渡网络科技有限公司实习做 AI 应用开发。有什么想了解的吗？

问：缺点
答：我的缺点是有时候过于追求完美，这可能会导致我在项目中花费更多时间去优化细节。不过，我也在学习如何在保证质量的同时提高效率。

问：职业规划
答：我的职业规划是在未来几年内成为一名技术精湛的 AI 开发工程师，专注于提升 AI 技术在不同领域的应用效率和用户体验。

【对话历史】
{history}

【面试官问题】
{question}

我的回答："""


RECOMMEND_QUESTION_PROMPT = """你是资深面试官。基于候选人的简历和当前对话历史，推荐 {n} 个值得深入考察的面试问题。

【要求】
- 优先考察候选人简历上没明确体现的能力（如系统设计、压力测试、协作）
- 结合当前对话上下文，避免重复已问过的角度
- 问题要具体、有深度
- 每个问题附 1 句「考察意图」说明

【候选人概要】
{profile_summary}

【当前对话历史】
{history}

【可选 JD 文本】
{jd_text}

【输出格式】
1. <问题> —— <考察意图>
2. <问题> —— <考察意图>
...
"""


def get_llm_config() -> dict:
    return {
        "api_key": LLM_API_KEY,
        "base_url": LLM_BASE_URL,
    }


def validate_config() -> list[str]:
    missing = []
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY")
    if not EMBEDDING_API_KEY:
        missing.append("EMBEDDING_API_KEY")
    return missing


if __name__ == "__main__":
    missing = validate_config()
    if missing:
        print(f"⚠️  缺少环境变量：{', '.join(missing)}")
        print("请复制 .env.example 为 .env 并填入对应 API Key")
    else:
        print("✅ 配置校验通过")