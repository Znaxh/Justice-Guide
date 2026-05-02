from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import StreamingResponse

from src import config
from src import prompts
from src.observability import get_metrics_snapshot, record_request, start_observability
from src.pipeline import arun_rag, astream_rag, get_cache_stats
from src.retrieval import ensure_index_loaded, rebuild_index

logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[])

# ---------------------------------------------------------------------------
# Session management (in-memory, per-process)
# ---------------------------------------------------------------------------

@dataclass
class ConversationMessage:
    role: str
    content: str


@dataclass
class Session:
    messages: list[ConversationMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)


_sessions: dict[str, Session] = {}
_sessions_lock = threading.Lock()


def _get_or_create_session(session_id: str | None) -> tuple[str, Session]:
    with _sessions_lock:
        _cleanup_expired_sessions()
        if session_id and session_id in _sessions:
            session = _sessions[session_id]
            session.last_active = time.time()
            return session_id, session
        new_id = str(uuid.uuid4())
        session = Session()
        _sessions[new_id] = session
        return new_id, session


def _cleanup_expired_sessions() -> None:
    now = time.time()
    expired = [k for k, v in _sessions.items() if now - v.last_active > config.SESSION_TTL]
    for k in expired:
        del _sessions[k]


def _session_history(session: Session) -> list[dict[str, str]] | None:
    if not session.messages:
        return None
    return [{"role": m.role, "content": m.content} for m in session.messages]


def _append_to_session(session: Session, query: str, answer: str) -> None:
    session.messages.append(ConversationMessage(role="user", content=query))
    session.messages.append(ConversationMessage(role="assistant", content=answer))
    max_entries = config.MAX_SESSION_MESSAGES * 2
    if len(session.messages) > max_entries:
        session.messages = session.messages[-max_entries:]


# ---------------------------------------------------------------------------
# Eval jobs
# ---------------------------------------------------------------------------

eval_jobs: dict[str, dict[str, Any]] = {}
eval_jobs_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not config.ADMIN_API_KEY:
        logger.warning(
            "admin_key_not_set",
            message="ADMIN_API_KEY is not configured. All /api/admin/* routes will return 403.",
            hint="Set ADMIN_API_KEY in your .env file to enable admin endpoints.",
        )
    start_observability()
    loop = asyncio.get_running_loop()

    async def _prewarm_index() -> None:
        try:
            await loop.run_in_executor(None, ensure_index_loaded)
            logger.info("lifespan.index_prewarmed")
        except Exception:
            logger.exception("lifespan.index_prewarm_failed")

    # Bind HTTP immediately so Render detects PORT; first request waits on retrieval lock if still loading.
    asyncio.create_task(_prewarm_index())
    yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=429,
        content={
            "ok": False,
            "error": "rate_limited",
            "message": "Too many requests. Please wait a moment before trying again.",
            "retry_after_seconds": 60,
            "disclaimer": config.DISCLAIMER,
        },
        headers={"X-Request-ID": rid},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AskBody(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: str | None = None


# ---------------------------------------------------------------------------
# Health / metrics
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "gemini_configured": bool(config.GEMINI_API_KEY),
        "groq_configured": bool(config.GROQ_API_KEY),
    }


@app.get("/api/metrics")
async def metrics():
    return {**get_metrics_snapshot(), "cache": get_cache_stats()}


# ---------------------------------------------------------------------------
# Debug / admin
# ---------------------------------------------------------------------------

async def _probe_provider(provider: str) -> dict[str, Any]:
    if provider == "gemini":
        if not config.GEMINI_API_KEY:
            return {"configured": False, "reachable": False, "model": config.GEMINI_MODEL, "error": None}
        llm = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GEMINI_API_KEY,
            temperature=0,
        )
        model_name = config.GEMINI_MODEL
    elif provider == "groq":
        if not config.GROQ_API_KEY:
            return {"configured": False, "reachable": False, "model": config.GROQ_MODEL, "error": None}
        llm = ChatGroq(
            model=config.GROQ_MODEL,
            groq_api_key=config.GROQ_API_KEY,
            temperature=0,
        )
        model_name = config.GROQ_MODEL
    else:
        raise ValueError(f"Unknown provider: {provider}")

    try:
        await asyncio.wait_for(llm.ainvoke("Health check: reply with OK."), timeout=12.0)
        return {"configured": True, "reachable": True, "model": model_name, "error": None}
    except Exception as exc:
        return {
            "configured": True,
            "reachable": False,
            "model": model_name,
            "error": f"{type(exc).__name__}: {str(exc)}",
        }


def _admin_key_ok(request: Request) -> bool:
    if not config.ADMIN_API_KEY:
        return False
    return request.headers.get("X-Admin-Key") == config.ADMIN_API_KEY


@app.get("/api/debug/providers")
async def debug_providers(request: Request):
    if not _admin_key_ok(request):
        raise HTTPException(status_code=403, detail="Forbidden")

    gemini, groq = await asyncio.gather(
        _probe_provider("gemini"),
        _probe_provider("groq"),
    )
    return {
        "ok": True,
        "gemini": gemini,
        "groq": groq,
        "disclaimer": config.DISCLAIMER,
    }


@app.post("/api/admin/rebuild-index")
async def admin_rebuild_index(request: Request):
    if not _admin_key_ok(request):
        raise HTTPException(status_code=403, detail="Forbidden")

    def worker():
        rebuild_index()

    threading.Thread(target=worker, daemon=True).start()
    return {"ok": True, "message": "Index rebuild started in background"}


@app.post("/api/admin/run-evals")
async def admin_run_evals(request: Request):
    if not _admin_key_ok(request):
        raise HTTPException(status_code=403, detail="Forbidden")
    from src.evals.eval_pipeline import run_evals_job

    job_id = str(uuid.uuid4())
    with eval_jobs_lock:
        eval_jobs[job_id] = {"status": "running", "result_path": None, "error": None}

    def worker():
        try:
            path = run_evals_job()
            with eval_jobs_lock:
                eval_jobs[job_id] = {"status": "done", "result_path": path, "error": None}
        except Exception as exc:
            logger.error("eval_job_failed", job_id=job_id, error=str(exc), exc_info=True)
            with eval_jobs_lock:
                eval_jobs[job_id] = {
                    "status": "failed",
                    "result_path": None,
                    "error": "Eval job failed. Check server logs for details.",
                }

    threading.Thread(target=worker, daemon=True).start()
    return {"job_id": job_id, "status": "running"}


@app.get("/api/admin/eval-results/{job_id}")
async def admin_eval_results(job_id: str, request: Request):
    if not _admin_key_ok(request):
        raise HTTPException(status_code=403, detail="Forbidden")
    with eval_jobs_lock:
        job = eval_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return job


# ---------------------------------------------------------------------------
# POST /api/ask  (non-streaming, with caching + sessions)
# ---------------------------------------------------------------------------

@app.post("/api/ask")
@limiter.limit(config.RATE_LIMIT)
async def ask(request: Request, body: AskBody):
    session_id, session = _get_or_create_session(body.session_id)
    history = _session_history(session)

    try:
        out = await asyncio.wait_for(
            arun_rag(body.query, history=history),
            timeout=config.ASK_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={
                "ok": False,
                "error": "timeout",
                "message": "Request timed out. Try a shorter query.",
                "prompt_version": prompts.VERSION,
                "disclaimer": config.DISCLAIMER,
            },
        )
    except Exception:
        logger.info("api.ask_unhandled")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "request_failed",
                "message": "An error occurred processing your request",
                "prompt_version": prompts.VERSION,
                "disclaimer": config.DISCLAIMER,
            },
        )

    if not out.get("ok"):
        return JSONResponse(
            status_code=502,
            content={
                "ok": False,
                "error": out.get("error") or "request_failed",
                "message": out.get("message") or "An error occurred processing your request",
                "disclaimer": config.DISCLAIMER,
                "prompt_version": out.get("prompt_version") or prompts.VERSION,
            },
        )

    _append_to_session(session, body.query, out["answer"])

    record_request(
        query=body.query,
        enhanced_query=out.get("enhanced_query") or "",
        num_chunks_retrieved=int(out.get("num_chunks") or 0),
        answer_length=len(out.get("answer") or ""),
        latency_ms=float(out.get("latency_ms") or 0),
        prompt_version=out.get("prompt_version") or "",
        llm_used=out.get("llm_used") or "unknown",
        estimated_tokens=out.get("estimated_tokens"),
        used_fallback=bool(out.get("used_fallback")),
    )

    return {
        "ok": True,
        "session_id": session_id,
        "answer": out["answer"],
        "citations": out.get("citations", []),
        "bns_notes": out.get("bns_notes", []),
        "enhanced_query": out.get("enhanced_query"),
        "prompt_version": out.get("prompt_version"),
        "estimated_tokens": out.get("estimated_tokens"),
        "llm_used": out.get("llm_used"),
        "disclaimer": config.DISCLAIMER,
    }


# ---------------------------------------------------------------------------
# POST /api/ask/stream  (SSE streaming with sessions)
# ---------------------------------------------------------------------------

@app.post("/api/ask/stream")
@limiter.limit(config.RATE_LIMIT)
async def ask_stream(request: Request, body: AskBody):
    session_id, session = _get_or_create_session(body.session_id)
    history = _session_history(session)

    async def event_generator():
        full_answer = ""
        try:
            async for event in astream_rag(body.query, history=history):
                if event["event"] == "token":
                    full_answer += event["data"]["text"]

                if event["event"] == "done":
                    event["data"]["session_id"] = session_id

                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"

            if full_answer:
                _append_to_session(session, body.query, full_answer)

        except Exception as exc:
            logger.error("api.stream_generator_error", error=str(exc))
            yield f"event: error\ndata: {json.dumps({'message': 'Stream failed unexpectedly.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
