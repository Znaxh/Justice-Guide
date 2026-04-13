"""
LangChain LCEL RAG pipeline: Gemini primary, Groq fallback, lazy retrieval.

Equivalent to the spec’s RunnableParallel({context: enhanced|retriever, question: passthrough})
pattern, implemented as a single retrieve step so context/citations are computed once per query
(saves RAM and latency on 8GB machines).
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src import config
from src.observability import redact_query
from src.prompts import PROMPT_REGISTRY, VERSION
from src.retrieval import retrieve_cited_context

# Canonical prompts from registry (single place to swap versions)
QUERY_ENHANCEMENT_PROMPT: ChatPromptTemplate = PROMPT_REGISTRY["query_enhancement"]
ANSWER_PROMPT: ChatPromptTemplate = PROMPT_REGISTRY["answer_generation"]

logger = structlog.get_logger(__name__)


def _pipeline_exception_result(question: str) -> dict[str, Any]:
    """Shared error payload for sync/async pipeline exception paths."""
    return {
        "ok": False,
        "error": "request_failed",
        "message": "An error occurred processing your request",
        "answer": "",
        "citations": [],
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
    """Approximate token usage from LangChain message metadata (Gemini / Groq)."""
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


def _retrieve_sync(state: dict[str, Any]) -> dict[str, Any]:
    ctx, cites, n = retrieve_cited_context(state["enhanced_query"])
    return {
        **state,
        "context": ctx,
        "citations": cites,
        "num_chunks": n,
    }


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
        "enhanced_query": state.get("enhanced_query", ""),
        "num_chunks": state.get("num_chunks", 0),
        "prompt_version": VERSION,
        "estimated_tokens": None,
        "llm_used": "none",
        "used_fallback": False,
        "disclaimer": config.DISCLAIMER,
    }


def _success_result(
    state: dict[str, Any],
    ai: Any,
) -> dict[str, Any]:
    text = ai.content if isinstance(ai.content, str) else "".join(str(p) for p in ai.content)
    est, model_name, fb = _extract_usage_and_model(ai)
    _, has_fb = _get_llm()
    used_fallback = fb and has_fb
    return {
        "ok": True,
        "answer": text.strip(),
        "citations": state["citations"],
        "enhanced_query": state["enhanced_query"],
        "num_chunks": state["num_chunks"],
        "prompt_version": VERSION,
        "estimated_tokens": est,
        "llm_used": model_name,
        "used_fallback": used_fallback,
    }


def _answer_finalize(state: dict[str, Any]) -> dict[str, Any]:
    llm, _ = _get_llm()
    if llm is None:
        return _no_llm_result(state)

    chain = (ANSWER_PROMPT | llm).with_config(run_name="answer_generation")
    cfg = RunnableConfig(tags=["answer_generation"])
    ai = chain.invoke(
        {
            "context": state["context"],
            "question": state["question"],
            "enhanced_query": state["enhanced_query"],
        },
        config=cfg,
    )
    return _success_result(state, ai)


async def _answer_finalize_async(state: dict[str, Any]) -> dict[str, Any]:
    llm, _ = _get_llm()
    if llm is None:
        return _no_llm_result(state)

    chain = (ANSWER_PROMPT | llm).with_config(run_name="answer_generation")
    cfg = RunnableConfig(tags=["answer_generation"])
    ai = await chain.ainvoke(
        {
            "context": state["context"],
            "question": state["question"],
            "enhanced_query": state["enhanced_query"],
        },
        config=cfg,
    )
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


def run_rag_sync(question: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    llm, _ = _get_llm()
    enhance = build_enhance_chain()
    try:
        if llm is None:
            eq = question
        else:
            eq = enhance.invoke({"question": question})
        state = {
            "question": question,
            "enhanced_query": eq,
        }
        state = _retrieve_sync(state)
        out = _answer_finalize(state)
    except Exception as exc:
        logger.info(
            "pipeline.sync_failed",
            query_redacted=redact_query(question),
            error_type=type(exc).__name__,
        )
        return _pipeline_exception_result(question)
    out["latency_ms"] = (time.perf_counter() - t0) * 1000
    return out


async def arun_rag(question: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    llm, _ = _get_llm()
    enhance = build_enhance_chain()
    try:
        if llm is None:
            eq = question
        else:
            eq = await enhance.ainvoke({"question": question})
        state = {"question": question, "enhanced_query": eq}
        state = await _retrieve_async(state)
        out = await _answer_finalize_async(state)
    except Exception as exc:
        logger.info(
            "pipeline.async_failed",
            query_redacted=redact_query(question),
            error_type=type(exc).__name__,
        )
        return _pipeline_exception_result(question)
    out["latency_ms"] = (time.perf_counter() - t0) * 1000
    return out


def generate_answer(query: str) -> str:
    """Streamlit / legacy: returns plain answer text."""
    result = run_rag_sync(query)
    if not result.get("ok"):
        return result.get("message") or "Request failed."
    return result.get("answer") or ""
