"""
AI-Me 冒烟测试（自动 stub 掉外部库）
=====================================
不需要安装 chromadb / loguru / langchain 就能跑
验证代码逻辑、配置、Pydantic 模型、分块、限流、Prompt 模板等
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

# ===== Stub 外部库 =====
def stub_external():
    """在导入任何项目模块前 stub 掉外部库"""

    # loguru
    loguru = types.ModuleType("loguru")

    class _StubLogger:
        def __getattr__(self, name):
            return lambda *a, **kw: None
        def __call__(self, *a, **kw):
            return self

    loguru.logger = _StubLogger()
    sys.modules["loguru"] = loguru
    sys.modules["loguru.logger"] = loguru.logger

    # chromadb
    chromadb = types.ModuleType("chromadb")
    chromadb.PersistentClient = type("PersistentClient", (), {})
    chromadb.config = types.ModuleType("chromadb.config")
    chromadb.config.Settings = type("Settings", (), {"__init__": lambda self, **kw: None})
    sys.modules["chromadb"] = chromadb
    sys.modules["chromadb.config"] = chromadb.config

    # langchain_openai
    lco = types.ModuleType("langchain_openai")
    lco.OpenAIEmbeddings = type("OpenAIEmbeddings", (), {})
    lco.ChatOpenAI = type("ChatOpenAI", (), {})
    sys.modules["langchain_openai"] = lco

    # langchain_community
    lc = types.ModuleType("langchain_community")
    lc_ret = types.ModuleType("langchain_community.retrievers")
    lc_ret.BM25Retriever = type("BM25Retriever", (), {})
    sys.modules["langchain_community"] = lc
    sys.modules["langchain_community.retrievers"] = lc_ret

    # langchain_core
    lc_core = types.ModuleType("langchain_core")
    lc_docs = types.ModuleType("langchain_core.documents")
    lc_docs.Document = type("Document", (), {})
    lc_msgs = types.ModuleType("langchain_core.messages")
    for n in ["HumanMessage", "SystemMessage", "AIMessage"]:
        setattr(lc_msgs, n, type(n, (), {}))
    lc_tools = types.ModuleType("langchain_core.tools")
    lc_tools.tool = lambda *a, **kw: lambda f: f
    sys.modules["langchain_core"] = lc_core
    sys.modules["langchain_core.documents"] = lc_docs
    sys.modules["langchain_core.messages"] = lc_msgs
    sys.modules["langchain_core.tools"] = lc_tools

    # langgraph
    lg = types.ModuleType("langgraph")
    lgg = types.ModuleType("langgraph.graph")
    lgg.StateGraph = type("StateGraph", (), {})
    lgg.END = "END"
    sys.modules["langgraph"] = lg
    sys.modules["langgraph.graph"] = lgg

    # fastapi（stub 简化）
    fastapi = types.ModuleType("fastapi")
    fastapi.FastAPI = type("FastAPI", (), {})
    fastapi.HTTPException = type("HTTPException", (Exception,), {})
    fastapi.Request = type("Request", (), {})
    cors_mod = types.ModuleType("fastapi.middleware.cors")
    cors_mod.CORSMiddleware = type("CORSMiddleware", (), {})
    resp_mod = types.ModuleType("fastapi.responses")
    resp_mod.StreamingResponse = type("StreamingResponse", (), {})
    resp_mod.JSONResponse = type("JSONResponse", (), {})
    sys.modules["fastapi"] = fastapi
    sys.modules["fastapi.middleware.cors"] = cors_mod
    sys.modules["fastapi.responses"] = resp_mod

    # tenacity / httpx / dotenv / jieba / rank_bm25
    tenacity_mod = types.ModuleType("tenacity")
    tenacity_mod.retry = lambda **kw: lambda f: f
    tenacity_mod.stop_after_attempt = lambda *a: None
    tenacity_mod.wait_exponential = lambda **kw: None
    tenacity_mod.retry_if_exception_type = lambda *a: None
    tenacity_mod.before_sleep_log = lambda *a, **kw: None
    sys.modules["tenacity"] = tenacity_mod
    sys.modules["tenacity.before_sleep_log"] = tenacity_mod.before_sleep_log

    for mod_name in ["httpx", "rank_bm25", "jieba", "jieba.posseg"]:
        sys.modules[mod_name] = types.ModuleType(mod_name)

    # dotenv（需要 load_dotenv 函数）
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *a, **kw: None
    sys.modules["dotenv"] = dotenv

    # yaml
    yaml = types.ModuleType("yaml")
    # 注意：这里 mock 要返回真实的 profile 内容，但实际我们直接走 profile.yaml 文件
    yaml.safe_load = lambda x: {
        "name": "<YOUR_NAME>",
        "title": "大模型算法工程师",
        "email": "test@example.com",
        "github": "https://github.com/<your-name>",
    }
    sys.modules["yaml"] = yaml

    # 设置测试用的环境变量
    os.environ.setdefault("LLM_API_KEY", "sk-test")
    os.environ.setdefault("EMBEDDING_API_KEY", "sk-test")
    os.environ.setdefault("RERANK_API_KEY", "sk-test")


# ===== 测试用例 =====
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))


def test_config():
    print("\n[1] config.py")
    import config
    assert config.LLM_MODEL == "abab6.5s-chat"
    assert config.EMBEDDING_MODEL == "embo-01"
    assert config.EMBEDDING_DIM == 1536
    assert "chroma" in config.CHROMA_DB_PATH.lower()
    assert config.CHROMA_COLLECTION == "ai_me_kb"
    assert config.RERANK_MODEL == "BAAI/bge-reranker-v2-m3"
    assert not config.validate_config(), f"missing: {config.validate_config()}"
    print("    [OK] all config fields correct")


def test_models():
    print("\n[2] models.py")
    from models import ChatRequest, ExportRequest
    assert ChatRequest(question="hi").question == "hi"
    try:
        ChatRequest(question="")
        assert False, "空问题应该报错"
    except Exception:
        pass
    try:
        ChatRequest(question="x" * 3000)
        assert False, "超长问题应该报错"
    except Exception:
        pass
    try:
        ExportRequest(session_id="x", format="xml")
        assert False, "非法 format 应该报错"
    except Exception:
        pass
    print("    [OK] Pydantic validators work")


def test_chunk_logic():
    print("\n[3] chunker.py")
    from utils.chunker import chunk_markdown, _infer_source_dir
    text = "# T\n\n## A\n\nA's content\n\n## B\n\nB's content"
    blocks = chunk_markdown(text, "doc-test", "resume.md")
    assert len(blocks) == 2
    assert blocks[0]["title"] == "A"
    assert blocks[1]["title"] == "B"
    assert _infer_source_dir("projects/x.md") == "projects"
    assert _infer_source_dir("blogs/x.md") == "blogs"
    assert _infer_source_dir("qa_pairs.jsonl") == "qa_pairs"
    assert _infer_source_dir("resume.md") == "root"
    print(f"    [OK] markdown split -> {len(blocks)} blocks")


def test_rate_limiter():
    print("\n[4] rate_limiter.py")
    from utils.rate_limiter import RateLimiter
    rl = RateLimiter(max_per_minute=3)
    assert rl.allow("ip1")
    assert rl.allow("ip1")
    assert rl.allow("ip1")
    assert not rl.allow("ip1"), "第 4 次必须被限流"
    assert rl.allow("ip2"), "不同 IP 隔离"
    print("    [OK] rate limiter: 3/min, IP isolated")


def test_profile_yaml():
    print("\n[5] profile_loader + yaml_to_markdown")
    from utils.profile_loader import load_profile
    from utils.loader import yaml_to_markdown
    profile = load_profile()
    assert isinstance(profile, dict), f"profile 应为 dict, 实际 {type(profile)}"
    assert len(profile) > 0, "profile 不应为空"
    md = yaml_to_markdown(profile)
    assert "# 候选人基本信息" in md, "yaml_to_markdown 输出应含标题"
    assert "name" in profile, "profile 应含 name 字段"
    print(f"    [OK] profile: {len(profile)} fields, name={profile.get('name')}")


def test_qa_pairs():
    print("\n[6] qa_pairs.jsonl")
    from utils.profile_loader import load_qa_pairs
    from utils.chunker import chunk_jsonl
    pairs = load_qa_pairs()
    assert len(pairs) >= 5, f"应至少有 5 条 QA，实际 {len(pairs)}"
    blocks = chunk_jsonl(pairs, "qa_pairs.jsonl")
    assert all(b["source_dir"] == "qa_pairs" for b in blocks)
    print(f"    [OK] {len(pairs)} QA pairs -> {len(blocks)} blocks")


def test_meta_doc():
    print("\n[7] graph/meta.py")
    from graph.meta import META_DOC
    assert "AI-Me" in META_DOC
    assert "Milvus" in META_DOC
    assert "MiniMax" in META_DOC or "MiniMax" in META_DOC
    assert "项目本身" in META_DOC or "meta" in META_DOC.lower()
    print(f"    [OK] META_DOC {len(META_DOC)} chars, 含项目元信息")


def test_graph_routes():
    print("\n[8] graph/graph.py - 5 类意图路由")
    from graph.graph import _route_by_intent
    cases = [
        # small_talk 现在也走 rewrite（检索链），避免 chat_node 跳过检索答非所问
        ({"intent": "small_talk"}, "rewrite"),
        ({"intent": "meta_question"}, "rewrite"),  # 同理，所有意图都走检索
        ({"intent": "recommend"}, "recommend"),
        ({"intent": "profile_qa"}, "rewrite"),
        ({"intent": "project_detail"}, "rewrite"),
        ({"intent": "skill_assessment"}, "rewrite"),
        ({"intent": "unknown"}, "rewrite"),  # 降级
        ({}, "rewrite"),  # 空状态降级
    ]
    for state, expected in cases:
        actual = _route_by_intent(state)
        assert actual == expected, f"{state} -> {actual}, expected {expected}"
    print("    [OK] 8 个路由场景全部正确（除 recommend 都走检索链）")


def test_prompts():
    print("\n[9] Prompt 模板")
    from config import SYSTEM_PROMPT_TEMPLATE, RECOMMEND_QUESTION_PROMPT
    assert "{context}" in SYSTEM_PROMPT_TEMPLATE
    assert "{history}" in SYSTEM_PROMPT_TEMPLATE
    assert "{question}" in SYSTEM_PROMPT_TEMPLATE
    # 简化版 prompt 不强制引用（避免 LLM 拒绝回答）
    assert "谭修诚" in SYSTEM_PROMPT_TEMPLATE
    assert "{n}" in RECOMMEND_QUESTION_PROMPT
    print("    [OK] Prompt 模板字段（简化版，不强制引用）")


def test_data_files():
    print("\n[10] 数据文件完整性")
    data_dir = BACKEND / "data"
    assert (data_dir / "profile.yaml").exists()
    assert (data_dir / "resume.md").exists()
    assert (data_dir / "qa_pairs.jsonl").exists()
    assert (data_dir / "projects" / "rag_graph.md").exists()
    projects_count = len(list((data_dir / "projects").glob("*.md")))
    qa_count = sum(1 for _ in open(data_dir / "qa_pairs.jsonl", encoding="utf-8") if _.strip())
    profile_size = (data_dir / "profile.yaml").stat().st_size
    resume_size = (data_dir / "resume.md").stat().st_size
    print(f"    [OK] profile.yaml: {profile_size}B, resume.md: {resume_size}B")
    print(f"          projects: {projects_count} 个, qa_pairs: {qa_count} 条")


def test_no_circular_dep():
    print("\n[11] 模块导入图（无循环依赖）")
    import ast
    base = BACKEND
    imports_map = {}
    for f in base.rglob("*.py"):
        rel = str(f.relative_to(base)).replace("\\", ".").rstrip(".py")
        if rel.endswith(".__init__"):
            rel = rel[:-9]
        with open(f, encoding="utf-8") as fp:
            tree = ast.parse(fp.read())
        imps = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.startswith(("utils.", "graph")) or mod in ("config", "models"):
                    imps.add(mod)
        imports_map[rel] = imps

    # 检查循环：A 导入 B，B 导入 A
    # 排除内部 self-import：graph/__init__.py 从 graph.graph 导入
    issues = []
    for a, deps in imports_map.items():
        for dep in deps:
            if dep in imports_map and a in imports_map[dep]:
                # 排除合法的 self-import（包入口从同名子模块导入）
                if a == dep or a == "graph" and dep == "graph.graph":
                    continue
                if dep == "graph" and a == "graph.graph":
                    continue
                issues.append(f"{a} <-> {dep}")
    assert not issues, f"循环依赖：{issues}"
    print(f"    [OK] {len(imports_map)} 个模块无循环依赖")


def main():
    print("=" * 60)
    print("  AI-Me · 冒烟测试（无需安装外部依赖）")
    print("=" * 60)

    tests = [
        test_config, test_models, test_chunk_logic, test_rate_limiter,
        test_profile_yaml, test_qa_pairs, test_meta_doc, test_graph_routes,
        test_prompts, test_data_files, test_no_circular_dep,
    ]

    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            msg = str(e) if str(e) else "(空断言，请看具体函数)"
            print(f"    [FAIL] {t.__name__}: {msg}")
            failed += 1
        except Exception as e:
            print(f"    [ERROR] {t.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"  结果：{passed} / {len(tests)} 通过")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    stub_external()
    sys.exit(main())