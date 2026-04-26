"""
LangChain LCEL RAG pipeline: Gemini primary, Groq fallback, lazy retrieval.
Now with SSE streaming, answer caching, BNS enrichment, and conversation history.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncGenerator

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src import config
from src.bns_mapping import bns_context_for_prompt, extract_bns_notes
from src.cache import TTLCache
from src.observability import redact_query
from src.prompts import PROMPT_REGISTRY, VERSION
from src.retrieval import retrieve_cited_context

QUERY_ENHANCEMENT_PROMPT: ChatPromptTemplate = PROMPT_REGISTRY["query_enhancement"]
ANSWER_PROMPT: ChatPromptTemplate = PROMPT_REGISTRY["answer_generation"]

logger = structlog.get_logger(__name__)

_answer_cache = TTLCache(maxsize=config.CACHE_MAXSIZE, ttl=config.CACHE_TTL)


def get_cache_stats() -> dict[str, int]:
    return _answer_cache.stats()


def _pipeline_exception_result(question: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": "request_failed",
        "message": "An error occurred processing your request",
        "answer": "",
        "citations": [],
        "bns_notes": [],
        "enhanced_query": question,
        "num_chunks": 0,
        "prompt_version": VERSION,
        "estimated_tokens": None,
        "llm_used": "unknown",
        "used_fallback": False,
        "disclaimer": config.DISCLAIMER,
    }


def _build_llm():
    primary = None
    fallback = None
    if config.GEMINI_API_KEY:
        primary = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GEMINI_API_KEY,
            temperature=0,
        )
    if config.GROQ_API_KEY:
        fallback = ChatGroq(
            model=config.GROQ_MODEL,
            groq_api_key=config.GROQ_API_KEY,
            temperature=0,
        )

    if primary and fallback:
        return primary.with_fallbacks([fallback]), True
    if primary:
        return primary, False
    if fallback:
        return fallback, False
    return None, False


_LLM: Runnable | None = None
_HAS_FALLBACK = False


def _get_llm():
    global _LLM, _HAS_FALLBACK
    if _LLM is None:
        _LLM, _HAS_FALLBACK = _build_llm()
    return _LLM, _HAS_FALLBACK


def _extract_usage_and_model(ai_message: Any) -> tuple[int | None, str, bool]:
    used_fallback = False
    model_name = ""
    est: int | None = None
    meta = getattr(ai_message, "response_metadata", None) or {}
    model_name = str(meta.get("model_name") or meta.get("model") or "")

    usage = getattr(ai_message, "usage_metadata", None)
    if usage is None:
        usage = meta.get("usage_metadata") or meta.get("token_usage") or {}
    if isinstance(usage, dict):
        est = usage.get("total_tokens")
        if est is None and "input_tokens" in usage and "output_tokens" in usage:
            est = int(usage["input_tokens"] or 0) + int(usage["output_tokens"] or 0)

    low = model_name.lower()
    if "llama" in low or "groq" in low or "mixtral" in low:
        used_fallback = True
    return est, model_name or "unknown", used_fallback


def _enhance_input(state: dict[str, Any]) -> dict[str, str]:
    q = state.get("question") or state.get("query")
    if q is None:
        raise KeyError("question or query")
    return {"query": q}


def _format_history(history: list[dict[str, str]] | None) -> str:
    if not history:
        return ""
    lines = ["Previous conversation:\n"]
    for msg in history[-(config.MAX_SESSION_MESSAGES * 2) :]:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        if len(content) > 500:
            content = content[:500] + "…"
        lines.append(f"{role}: {content}\n")
    lines.append("\nNow answer the current question:\n")
    return "".join(lines)


def _contextualize_query(question: str, history: list[dict[str, str]] | None) -> str:
    """Prepend recent conversation context so the enhancer/retriever can
    resolve follow-up pronouns like 'its', 'that', 'the same'."""
    if not history:
        return question
    recent = history[-2:]
    parts = []
    for m in recent:
        prefix = "Q" if m["role"] == "user" else "A"
        snippet = m["content"][:200]
        parts.append(f"{prefix}: {snippet}")
    return f"[Previous: {' | '.join(parts)}] {question}"


async def _retrieve_async(state: dict[str, Any]) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    ctx, cites, n = await loop.run_in_executor(
        None, lambda: retrieve_cited_context(state["enhanced_query"])
    )
    return {
        **state,
        "context": ctx,
        "citations": cites,
        "num_chunks": n,
    }


def _no_llm_result(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": False,
        "error": "no_llm",
        "message": "No LLM configured. Set GEMINI_API_KEY and/or GROQ_API_KEY.",
        "answer": "",
        "citations": state.get("citations", []),
        "bns_notes": state.get("bns_notes", []),
        "enhanced_query": state.get("enhanced_query", ""),
        "num_chunks": state.get("num_chunks", 0),
        "prompt_version": VERSION,
        "estimated_tokens": None,
        "llm_used": "none",
        "used_fallback": False,
        "disclaimer": config.DISCLAIMER,
    }


def _success_result(state: dict[str, Any], ai: Any) -> dict[str, Any]:
    text = ai.content if isinstance(ai.content, str) else "".join(str(p) for p in ai.content)
    est, model_name, fb = _extract_usage_and_model(ai)
    _, has_fb = _get_llm()
    used_fallback = fb and has_fb
    return {
        "ok": True,
        "answer": text.strip(),
        "citations": state["citations"],
        "bns_notes": state.get("bns_notes", []),
        "enhanced_query": state["enhanced_query"],
        "num_chunks": state["num_chunks"],
        "prompt_version": VERSION,
        "estimated_tokens": est,
        "llm_used": model_name,
        "used_fallback": used_fallback,
    }


async def _answer_finalize_async(state: dict[str, Any]) -> dict[str, Any]:
    llm, _ = _get_llm()
    if llm is None:
        return _no_llm_result(state)

    payload = {
        "context": state["context"],
        "question": state["question"],
        "enhanced_query": state["enhanced_query"],
        "history": state.get("history_text", ""),
    }
    cfg = RunnableConfig(tags=["answer_generation"])
    chain = (ANSWER_PROMPT | llm).with_config(run_name="answer_generation")
    try:
        ai = await chain.ainvoke(payload, config=cfg)
    except Exception as exc:
        if config.GROQ_API_KEY:
            logger.warning(
                "pipeline.answer_primary_failed_retrying_groq",
                error_type=type(exc).__name__,
                error=str(exc),
            )
            groq_llm = ChatGroq(
                model=config.GROQ_MODEL,
                groq_api_key=config.GROQ_API_KEY,
                temperature=0,
            )
            groq_chain = (ANSWER_PROMPT | groq_llm).with_config(
                run_name="answer_generation_groq_retry"
            )
            ai = await groq_chain.ainvoke(payload, config=cfg)
        else:
            raise
    return _success_result(state, ai)


def build_enhance_chain() -> Runnable:
    llm, _ = _get_llm()
    if llm is None:

        def _noop(s: dict[str, Any]) -> str:
            v = s.get("question") or s.get("query")
            if v is None:
                raise KeyError("question or query")
            return str(v)

        return RunnableLambda(_noop)

    return (
        RunnableLambda(_enhance_input)
        | QUERY_ENHANCEMENT_PROMPT
        | llm
        | StrOutputParser()
    ).with_config(run_name="query_enhancement")


# ---------------------------------------------------------------------------
# Non-streaming entry point (with caching)
# ---------------------------------------------------------------------------

async def arun_rag(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if not history:
        cache_key = _answer_cache.make_key(question)
        cached = _answer_cache.get(cache_key)
        if cached is not None:
            logger.info("pipeline.cache_hit", query_redacted=redact_query(question))
            return cached

    t0 = time.perf_counter()
    llm, _ = _get_llm()
    enhance = build_enhance_chain()
    contextual_q = _contextualize_query(question, history)
    try:
        if llm is None:
            eq = contextual_q
        else:
            try:
                eq = await enhance.ainvoke({"question": contextual_q})
            except Exception as exc:
                logger.warning(
                    "pipeline.enhancement_failed_using_raw_query",
                    query_redacted=redact_query(question),
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
                eq = contextual_q

        state: dict[str, Any] = {
            "question": question,
            "enhanced_query": eq,
            "history_text": _format_history(history),
        }
        state = await _retrieve_async(state)

        bns_extra = bns_context_for_prompt(eq, state["context"])
        if bns_extra:
            state["context"] += bns_extra
        state["bns_notes"] = extract_bns_notes(eq + "\n" + state["context"])

        out = await _answer_finalize_async(state)
    except Exception as exc:
        logger.info(
            "pipeline.async_failed",
            query_redacted=redact_query(question),
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return _pipeline_exception_result(question)

    out["latency_ms"] = (time.perf_counter() - t0) * 1000

    if not history and out.get("ok"):
        _answer_cache.put(cache_key, out)

    return out


# ---------------------------------------------------------------------------
# SSE streaming entry point
# ---------------------------------------------------------------------------

def _sse(event: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"event": event, "data": data}


async def astream_rag(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield SSE event dicts for streaming RAG responses."""
    t0 = time.perf_counter()
    llm, _ = _get_llm()
    enhance = build_enhance_chain()

    # Phase 1: query enhancement (with conversation context for follow-ups)
    contextual_q = _contextualize_query(question, history)
    yield _sse("status", {"phase": "enhancing"})
    try:
        if llm is None:
            eq = contextual_q
        else:
            try:
                eq = await enhance.ainvoke({"question": contextual_q})
            except Exception:
                eq = contextual_q
    except Exception:
        eq = contextual_q

    # Phase 2: retrieval
    yield _sse("status", {"phase": "retrieving"})
    try:
        loop = asyncio.get_running_loop()
        ctx, cites, n = await loop.run_in_executor(
            None, lambda: retrieve_cited_context(eq)
        )
    except Exception as exc:
        logger.warning("pipeline.stream_retrieval_failed", error=str(exc))
        yield _sse("error", {"message": "Retrieval failed. Please try again."})
        return

    bns_extra = bns_context_for_prompt(eq, ctx)
    if bns_extra:
        ctx += bns_extra
    bns_notes = extract_bns_notes(eq + "\n" + ctx)

    yield _sse("citations", {"citations": cites, "bns_notes": bns_notes})

    # Phase 3: stream answer generation
    if llm is None:
        yield _sse("error", {"message": "No LLM configured. Set GEMINI_API_KEY and/or GROQ_API_KEY."})
        return

    yield _sse("status", {"phase": "generating"})

    payload = {
        "context": ctx,
        "question": question,
        "enhanced_query": eq,
        "history": _format_history(history),
    }
    cfg = RunnableConfig(tags=["answer_generation"])
    chain = (ANSWER_PROMPT | llm).with_config(run_name="answer_generation")

    full_text = ""
    llm_used = "unknown"
    try:
        async for chunk in chain.astream(payload, config=cfg):
            token = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            if token:
                full_text += token
                yield _sse("token", {"text": token})
            meta = getattr(chunk, "response_metadata", None) or {}
            if meta.get("model_name") or meta.get("model"):
                llm_used = str(meta.get("model_name") or meta.get("model"))
    except Exception as exc:
        logger.warning("pipeline.stream_primary_failed", error=str(exc))
        if config.GROQ_API_KEY:
            groq_llm = ChatGroq(
                model=config.GROQ_MODEL,
                groq_api_key=config.GROQ_API_KEY,
                temperature=0,
            )
            groq_chain = (ANSWER_PROMPT | groq_llm).with_config(
                run_name="answer_generation_groq_retry"
            )
            full_text = ""
            llm_used = config.GROQ_MODEL
            try:
                async for chunk in groq_chain.astream(payload, config=cfg):
                    token = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                    if token:
                        full_text += token
                        yield _sse("token", {"text": token})
            except Exception as exc2:
                logger.error("pipeline.stream_all_failed", error=str(exc2))
                yield _sse("error", {"message": "All LLM providers failed. Please try again later."})
                return
        else:
            yield _sse("error", {"message": "LLM provider failed. Please try again later."})
            return

    latency = (time.perf_counter() - t0) * 1000
    yield _sse("done", {
        "enhanced_query": eq,
        "latency_ms": round(latency, 2),
        "prompt_version": VERSION,
        "llm_used": llm_used,
        "disclaimer": config.DISCLAIMER,
    })
