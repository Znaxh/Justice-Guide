import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from src import config
from src import prompts


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    r = await async_client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "gemini_configured" in data


@pytest.mark.asyncio
async def test_ask_empty_query(async_client):
    r = await async_client.post("/api/ask", json={"query": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ask_valid_query(async_client):
    if os.getenv("RUN_GEMINI_E2E", "").lower() not in ("1", "true", "yes"):
        pytest.skip("Set RUN_GEMINI_E2E=1 and GEMINI_API_KEY for live LLM test")
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
    r = await async_client.post("/api/ask", json={"query": "What is IPC section 302?"})
    if r.status_code != 200:
        pytest.fail(f"Expected 200 from /api/ask, got {r.status_code}: {r.text}")
    data = r.json()
    assert data.get("ok") is True
    assert isinstance(data.get("answer"), str)
    assert len(data.get("answer", "").strip()) > 0


@pytest.mark.asyncio
async def test_disclaimer_present(async_client, monkeypatch):
    async def _fast_rag(_q: str):
        return {
            "ok": True,
            "answer": "stub",
            "citations": [],
            "enhanced_query": _q,
            "num_chunks": 0,
            "prompt_version": prompts.VERSION,
            "estimated_tokens": 1,
            "llm_used": "test",
            "used_fallback": False,
            "latency_ms": 0.1,
        }

    monkeypatch.setattr("src.main.arun_rag", _fast_rag)
    r = await async_client.post("/api/ask", json={"query": "What is IPC section 302?"})
    data = r.json()
    assert data.get("disclaimer") == config.DISCLAIMER


@pytest.mark.asyncio
async def test_prompt_version_in_error_response(async_client):
    """504 responses must include prompt_version (regression for audit finding)."""

    with patch("src.main.arun_rag", new_callable=AsyncMock) as mock_rag:
        mock_rag.side_effect = asyncio.TimeoutError
        response = await async_client.post("/api/ask", json={"query": "test"})
    assert response.status_code == 504
    data = response.json()
    assert "prompt_version" in data
    assert data["prompt_version"] == prompts.VERSION


@pytest.mark.asyncio
async def test_config_values_used_in_response(async_client, monkeypatch):
    """API response fields must match config constants, not hardcoded strings."""

    async def stub(_q: str):
        return {
            "ok": True,
            "answer": "test answer",
            "citations": [],
            "enhanced_query": "test",
            "num_chunks": 0,
            "prompt_version": prompts.VERSION,
            "estimated_tokens": 1,
            "llm_used": "test",
            "used_fallback": False,
            "latency_ms": 0.1,
        }

    monkeypatch.setattr("src.main.arun_rag", stub)
    response = await async_client.post("/api/ask", json={"query": "What is IPC 302?"})
    assert response.status_code == 200
    data = response.json()
    assert data["disclaimer"] == config.DISCLAIMER
    assert data["prompt_version"] == prompts.VERSION


@pytest.mark.asyncio
async def test_rate_limit(async_client, monkeypatch):
    """Run last: exhausts the per-minute /api/ask quota for this client IP."""
    async def _fast_rag(_q: str):
        return {
            "ok": True,
            "answer": "ok",
            "citations": [],
            "enhanced_query": _q,
            "num_chunks": 0,
            "prompt_version": prompts.VERSION,
            "estimated_tokens": 1,
            "llm_used": "test",
            "used_fallback": False,
            "latency_ms": 0.1,
        }

    monkeypatch.setattr("src.main.arun_rag", _fast_rag)
    codes = []
    for _ in range(25):
        resp = await async_client.post("/api/ask", json={"query": "What is theft?"})
        codes.append(resp.status_code)
    assert 429 in codes
