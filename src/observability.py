"""Local Phoenix tracing, structlog, and in-memory request metrics."""

from __future__ import annotations

import os
import statistics
import threading
from collections import deque
from typing import Any

import structlog
from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register

from src import config

logger = structlog.get_logger(__name__)

_metrics_lock = threading.Lock()
_metrics: dict[str, Any] = {
    "total_requests": 0,
    "latencies_ms": deque(maxlen=config.METRICS_MAXLEN),
    "fallback_hits": 0,
}

_phoenix_started = False
_instrumented = False


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )


def redact_query(q: str) -> str:
    if len(q) <= 50:
        return q
    return q[:50] + "…"


def start_observability() -> None:
    """Start Phoenix UI (unless SKIP_PHOENIX) and instrument LangChain once."""
    global _phoenix_started, _instrumented
    configure_logging()

    if _instrumented:
        return

    if not config.SKIP_PHOENIX:
        if not _phoenix_started:
            try:
                import phoenix as px

                # launch_app(host=..., port=...) is deprecated; use env vars (Phoenix 13+).
                os.environ.setdefault("PHOENIX_HOST", "127.0.0.1")
                os.environ["PHOENIX_PORT"] = str(config.PHOENIX_PORT)

                def _launch() -> None:
                    px.launch_app()

                threading.Thread(target=_launch, daemon=True).start()
                _phoenix_started = True
                logger.info("observability.phoenix_started", port=config.PHOENIX_PORT)
            except Exception as exc:
                logger.warning(
                    "observability.phoenix_launch_failed",
                    error=str(exc),
                    port=config.PHOENIX_PORT,
                )

    if config.SKIP_PHOENIX:
        logger.info("observability.phoenix_skipped")
    else:
        tracer_provider = register(
            project_name="justice-guide",
            endpoint=config.PHOENIX_OTLP_ENDPOINT,
            batch=True,
        )
        LangChainInstrumentor(tracer_provider=tracer_provider).instrument(skip_dep_check=True)
        logger.info("observability.langchain_instrumented")
    _instrumented = True


def record_request(
    *,
    query: str,
    enhanced_query: str,
    num_chunks_retrieved: int,
    answer_length: int,
    latency_ms: float,
    prompt_version: str,
    llm_used: str,
    estimated_tokens: int | None,
    used_fallback: bool,
) -> None:
    with _metrics_lock:
        _metrics["total_requests"] += 1
        _metrics["latencies_ms"].append(latency_ms)
        if used_fallback:
            _metrics["fallback_hits"] += 1

    logger.info(
        "request.completed",
        query_redacted=redact_query(query),
        enhanced_query_redacted=redact_query(enhanced_query),
        num_chunks_retrieved=num_chunks_retrieved,
        answer_length=answer_length,
        latency_ms=round(latency_ms, 2),
        prompt_version=prompt_version,
        llm_used=llm_used,
        estimated_tokens=estimated_tokens,
        used_fallback=used_fallback,
    )


def get_metrics_snapshot() -> dict[str, Any]:
    with _metrics_lock:
        total = _metrics["total_requests"]
        latencies = list(_metrics["latencies_ms"])
        fb = _metrics["fallback_hits"]
    avg = statistics.mean(latencies) if latencies else 0.0
    p95 = 0.0
    if latencies:
        latencies_sorted = sorted(latencies)
        idx = max(0, int(round(0.95 * (len(latencies_sorted) - 1))))
        p95 = latencies_sorted[idx]
    fallback_rate = (fb / total) if total else 0.0
    return {
        "total_requests": total,
        "avg_latency_ms": round(avg, 2),
        "p95_latency_ms": round(p95, 2),
        "fallback_rate": round(fallback_rate, 4),
    }
