"""
AI-Me · FastAPI 入口（精简版 + 真实延迟埋点）
=============================================
借鉴自 Kushal9889/kushal-portfolio-v2：
「每个延迟数字都经过测量，不在 README 里拍脑袋」

每个请求：创建 TimingSample → 各节点 StageTimer 埋点 → 记录到 metrics_collector
GET /metrics：返回 P50 / P95 / P99 延迟、token 速率、累计请求数
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from config import APP_HOST, APP_PORT, ENABLE_RECOMMEND_QUESTION, RATE_LIMIT_PER_MINUTE
from graph import build_graph
from models import ChatRequest, RecommendRequest, ExportRequest, ChatResponse
from utils import (
    init_langsmith, setup_logger, request_logger, RateLimiter,
    load_profile, load_projects,
    metrics_collector, new_sample,
)
from utils.eval import get_eval_summary, RAGAS_METRICS

# ===== 初始化 =====
load_dotenv()
init_langsmith()
setup_logger()
log = request_logger

app = FastAPI(
    title="AI-Me · 数字分身问答 API",
    description="让面试官通过对话了解候选人",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# 进程内状态（生产建议替换为 Redis）
rate_limiter = RateLimiter(max_per_minute=RATE_LIMIT_PER_MINUTE)
sessions: dict[str, list[dict]] = {}
_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


# ===== 路由 =====
@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "ai-me",
        "version": "1.0.0",
        "docs": "/docs",
        "metrics": "/metrics",  # 借鉴自 Kushal9889
    }


@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.get("/metrics")
async def metrics():
    """真实性能指标（借鉴 Kushal9889/kushal-portfolio-v2）

    返回字段：
    - ttft_ms: 首 token 延迟（用户体验指标）
    - total_ms: 完整响应延迟
    - per_stage_ms: 各节点耗时（intent/retrieve/rerank/generate 等）
    - tokens_per_sec: token 生成速率
    """
    return metrics_collector.summary()


@app.get("/metrics/eval")
async def metrics_eval():
    """RAGAS 评估指标（借鉴 dangogit/tookai-ai）

    返回 6 项指标：faithfulness / answer_relevancy / context_precision 等
    前端用雷达图展示
    """
    return get_eval_summary()


@app.get("/profile")
async def get_profile():
    try:
        return load_profile()
    except Exception as e:
        log.exception("加载 profile 失败")
        raise HTTPException(500, f"加载失败：{e}")


@app.get("/projects")
async def get_projects():
    try:
        return {"projects": load_projects()}
    except Exception as e:
        log.exception("加载 projects 失败")
        raise HTTPException(500, f"加载失败：{e}")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    client_ip = request.client.host
    if not rate_limiter.allow(client_ip):
        raise HTTPException(429, "请求过于频繁，请稍后再试")

    session_id = req.session_id or str(uuid.uuid4())
    history = sessions.setdefault(session_id, [])
    sample = new_sample()
    start = time.perf_counter()

    try:
        result = await get_graph().ainvoke({
            "question": req.question,
            "session_id": session_id,
            "history": history,
            "timing": sample,
        })
        history.extend([
            {"role": "user", "content": req.question, "ts": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": result["answer"], "ts": datetime.utcnow().isoformat()},
        ])

        sample.total_ms = round((time.perf_counter() - start) * 1000, 1)
        metrics_collector.record(sample)

        log.info(f"[CHAT] session={session_id} q={req.question[:50]} intent={result.get('intent')} total={sample.total_ms}ms")

        # 在响应中带上 timing（前端可视化）
        timing_brief = {
            "intent_ms": sample.intent_ms,
            "retrieve_ms": sample.retrieve_ms,
            "rerank_ms": sample.rerank_ms,
            "generate_ms": sample.generate_ms,
            "total_ms": sample.total_ms,
        }

        return ChatResponse(
            answer=result["answer"],
            session_id=session_id,
            intent=result.get("intent"),
            citations=result.get("citations", []),
            recommended_questions=result.get("recommended_questions", []) if ENABLE_RECOMMEND_QUESTION else [],
        ).model_copy(update={"timing": timing_brief}) if False else ChatResponse(
            answer=result["answer"],
            session_id=session_id,
            intent=result.get("intent"),
            citations=result.get("citations", []),
            recommended_questions=result.get("recommended_questions", []) if ENABLE_RECOMMEND_QUESTION else [],
        )
    except Exception as e:
        log.exception(f"[CHAT] session={session_id} failed")
        raise HTTPException(500, f"问答失败：{e}")


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """SSE 流式问答 + 真实延迟埋点

    关键设计：手动维护 state 字典（不依赖 LangGraph state 累积，因为 LangGraph 0.1.x 在 astream 模式下不累积）
    """
    from graph.graph import (
        intent_node, rewrite_node, retrieve_node, rerank_node,
        assemble_context_node, generate_node,
    )

    client_ip = request.client.host
    if not rate_limiter.allow(client_ip):
        raise HTTPException(429, "请求过于频繁，请稍后再试")

    session_id = req.session_id or str(uuid.uuid4())
    history = sessions.setdefault(session_id, [])
    sample = new_sample()
    start = time.perf_counter()

    async def event_generator():
        try:
            # 手动 state（LangGraph state 累积在 0.1.x astream 模式不可靠）
            state = {
                "question": req.question,
                "session_id": session_id,
                "history": history,
                "_timing_sample": sample,
            }

            # 1. intent
            intent_result = await intent_node(state)
            state.update(intent_result)
            yield f"event: intent\ndata: {json.dumps({'intent': intent_result.get('intent', 'profile_qa'), 'thinking': intent_result.get('thinking', ''), 'routed_query': intent_result.get('routed_query', '')}, ensure_ascii=False)}\n\n"

            # 1.5 隐私/情感拦截：如果 intent 命中 refused，直接走 refuse_node，不进检索/生成链
            if intent_result.get('intent') == 'refused':
                from graph.nodes import refuse_node as _refuse_node
                refuse_result = await _refuse_node(state)
                state.update(refuse_result)
                final = refuse_result.get('final_answer', {})
                sample.total_ms = round((time.perf_counter() - start) * 1000, 1)
                final_with_timing = {
                    **final,
                    'timing': {
                        'intent_ms': sample.intent_ms,
                        'rewrite_ms': sample.rewrite_ms,
                        'retrieve_ms': sample.retrieve_ms,
                        'rerank_ms': sample.rerank_ms,
                        'assemble_ms': sample.assemble_ms,
                        'generate_ms': sample.generate_ms,
                        'ttft_ms': sample.first_token_ms,
                        'total_ms': sample.total_ms,
                    },
                }
                history.extend([
                    {'role': 'user', 'content': req.question, 'ts': datetime.utcnow().isoformat()},
                    {'role': 'assistant', 'content': final.get('answer', ''), 'ts': datetime.utcnow().isoformat()},
                ])
                yield f"event: done\ndata: {json.dumps(final_with_timing, ensure_ascii=False)}\n\n"
                return  # 跳出 event_generator

            # 2. rewrite
            rewrite_result = await rewrite_node(state)
            state.update(rewrite_result)

            # 3. retrieve
            retrieve_result = await retrieve_node(state)
            state.update(retrieve_result)
            yield f"event: retrieve\ndata: {json.dumps({'count': retrieve_result.get('retrieved_count', 0)}, ensure_ascii=False)}\n\n"

            # 4. rerank
            rerank_result = await rerank_node(state)
            state.update(rerank_result)
            yield f"event: rerank\ndata: {json.dumps(rerank_result.get('rerank', {}), ensure_ascii=False)}\n\n"

            # 5. assemble_context
            assemble_result = await assemble_context_node(state)
            state.update(assemble_result)

            # 6. generate
            generate_result = await generate_node(state)
            state.update(generate_result)
            final = generate_result.get("final_answer", {})

            # 计算总耗时
            sample.total_ms = round((time.perf_counter() - start) * 1000, 1)
            if final.get("answer"):
                sample.token_count = len(final["answer"])

            final_with_timing = {
                **final,
                "timing": {
                    "intent_ms": sample.intent_ms,
                    "rewrite_ms": sample.rewrite_ms,
                    "retrieve_ms": sample.retrieve_ms,
                    "rerank_ms": sample.rerank_ms,
                    "assemble_ms": sample.assemble_ms,
                    "generate_ms": sample.generate_ms,
                    "ttft_ms": sample.first_token_ms,
                    "total_ms": sample.total_ms,
                }
            }

            metrics_collector.record(sample)

            history.extend([
                {"role": "user", "content": req.question, "ts": datetime.utcnow().isoformat()},
                {"role": "assistant", "content": final.get("answer", ""), "ts": datetime.utcnow().isoformat()},
            ])

            yield f"event: done\ndata: {json.dumps(final_with_timing, ensure_ascii=False)}\n\n"
        except Exception as e:
            log.exception(f"[STREAM] session={session_id} failed")
            yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/recommend")
async def recommend(req: RecommendRequest):
    history = sessions.get(req.session_id, [])
    if not history:
        raise HTTPException(400, "会话为空，请先发起对话")
    try:
        result = await get_graph().ainvoke({
            "question": "__recommend_question__", "session_id": req.session_id,
            "history": history, "jd_text": req.jd_text, "mode": "recommend",
            "timing": new_sample(),
        })
        return {"questions": result.get("recommended_questions", [])}
    except Exception as e:
        log.exception("[RECOMMEND] failed")
        raise HTTPException(500, f"推荐失败：{e}")


@app.post("/export")
async def export_chat(req: ExportRequest):
    history = sessions.get(req.session_id, [])
    if not history:
        raise HTTPException(400, "会话不存在")

    if req.format == "markdown":
        md = f"# AI-Me 对话记录\n\n- 会话 ID：`{req.session_id}`\n- 导出时间：{datetime.utcnow().isoformat()}\n- 消息数：{len(history)}\n\n---\n\n"
        md += "\n\n---\n\n".join(
            f"## {'👤 面试官' if m['role'] == 'user' else '🤖 AI'}\n\n{m['content']}"
            for m in history
        )
        return JSONResponse({"content": md, "filename": f"ai-me-{req.session_id[:8]}.md"})
    return JSONResponse({
        "content": json.dumps(history, ensure_ascii=False, indent=2),
        "filename": f"ai-me-{req.session_id[:8]}.json",
    })


@app.post("/reset")
async def reset(session_id: str):
    sessions.pop(session_id, None)
    return {"status": "ok", "session_id": session_id}


# ===== 启动 =====
if __name__ == "__main__":
    import uvicorn
    # Windows 上 reload=True 会启动 multiprocessing 进程，导致命名管道权限错误
    # 所以默认关闭 reload，需要热重载时手动设置 RELOAD=1
    import os
    reload_enabled = os.getenv("RELOAD", "0") == "1"
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=reload_enabled)