from __future__ import annotations

import asyncio
import os
import threading
import uuid
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src import config
from src import prompts
from src.observability import get_metrics_snapshot, record_request, start_observability
from src.pipeline import arun_rag, run_rag_sync
from src.retrieval import rebuild_index

logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[])

eval_jobs: dict[str, dict[str, Any]] = {}
eval_jobs_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not config.ADMIN_API_KEY:
        logger.warning(
            "admin_key_not_set",
            message="ADMIN_API_KEY is not configured. All /api/admin/* routes will return 403.",
            hint="Set ADMIN_API_KEY in your .env file to enable admin endpoints.",
        )
    start_observability()
    yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limited",
            "message": "Too many requests",
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

template_folder_path = os.path.join(os.path.dirname(__file__), "..", "templates")
static_folder_path = os.path.join(os.path.dirname(__file__), "..", "static")
templates = Jinja2Templates(directory=template_folder_path)
app.mount("/static", StaticFiles(directory=static_folder_path), name="static")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


class AskBody(BaseModel):
    query: str = Field(..., min_length=1)


@app.get("/", response_class=HTMLResponse)
async def get_data(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/", response_class=HTMLResponse)
async def post_data(request: Request, Input: str = Form(...)):
    result = await asyncio.to_thread(run_rag_sync, Input)
    if not result.get("ok"):
        response_text = result.get("message") or "Request failed."
    else:
        response_text = result.get("answer") or ""
    data = {"message": response_text}
    return templates.TemplateResponse("index.html", {"request": request, "data": data})


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "gemini_configured": bool(config.GEMINI_API_KEY),
        "groq_configured": bool(config.GROQ_API_KEY),
    }


@app.get("/api/metrics")
async def metrics():
    return get_metrics_snapshot()


def _admin_key_ok(request: Request) -> bool:
    if not config.ADMIN_API_KEY:
        return False
    return request.headers.get("X-Admin-Key") == config.ADMIN_API_KEY


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


@app.post("/api/ask")
@limiter.limit(config.RATE_LIMIT)
async def ask(request: Request, body: AskBody):
    try:
        out = await asyncio.wait_for(
            arun_rag(body.query),
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
                "error": "request_failed",
                "message": "An error occurred processing your request",
                "disclaimer": config.DISCLAIMER,
                "prompt_version": out.get("prompt_version"),
            },
        )

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
        "answer": out["answer"],
        "citations": out.get("citations", []),
        "enhanced_query": out.get("enhanced_query"),
        "prompt_version": out.get("prompt_version"),
        "estimated_tokens": out.get("estimated_tokens"),
        "llm_used": out.get("llm_used"),
        "disclaimer": config.DISCLAIMER,
    }
