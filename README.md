# JusticeGuide — production RAG (IPC)

RAG legal Q&A over Indian Penal Code materials: **Google Gemini 1.5 Flash** (primary) with **Groq `llama3-8b-8192`** fallback, **LlamaIndex + FAISS** on-disk index (no pickle), **LangChain LCEL** pipeline, **Arize Phoenix** tracing, and **Ragas** evals.

## Architecture

```
                    +------------------+
                    |   POST /api/ask  |
                    +--------+---------+
                             |
                             v
              +------------------------------+
              |  query_enhancement (LCEL)    |  run_name: query_enhancement
              |  Gemini / Groq             |
              +--------------+-------------+
                             |
                             v
              +------------------------------+
              |  retriever (lazy)          |  run_name: retriever_faiss
              |  LlamaIndex CitationQE     |
              |  + FaissVectorStore        |
              +--------------+-------------+
                             |
                             v
              +------------------------------+
              |  answer_generation (LCEL)   |  run_name: answer_generation
              |  numbered context [1],[2]  |
              |  Gemini with Groq fallback   |
              +--------------+-------------+
                             |
                             v
                    JSON + citations
                             |
              +--------------+-------------+
              | Phoenix UI  | structlog    |
              | (optional)  | + metrics    |
              +-------------+--------------+
```

## Prerequisites

- Python **3.11–3.13** (see `requires-python` in `pyproject.toml`)
- [uv](https://docs.astral.sh/uv/) package manager
- Free API keys: [Google AI Studio (Gemini)](https://aistudio.google.com/apikey), [Groq](https://console.groq.com/keys)

`arize-phoenix` **14.x** pulls a **pre-release** `graphql-core`; `uv` is configured with `prerelease = "allow"` in `pyproject.toml` so locks resolve cleanly.

## Setup

```bash
cd Justice-Guide
cp .env.example .env   # fill GEMINI_API_KEY, GROQ_API_KEY, ADMIN_API_KEY, etc.
uv sync --all-groups   # include dev deps for tests
```

Place IPC PDFs under `dataset/` (optional nested `dataset/Indian Penal Code Book (2)_chunks/`). If no PDFs are found, a small in-sample index is built so the API still runs.

## Run the API

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

- **Phoenix** (tracing): open `http://127.0.0.1:6006` (override with `PHOENIX_PORT`). Set `SKIP_PHOENIX=1` to disable the UI thread (e.g. tests).
- **Streamlit** (optional UI): `uv run streamlit run streamlit_main.py`

### JSON ask endpoint

`POST /api/ask` with body `{"query": "..."}` — response includes `disclaimer`, `prompt_version`, `citations`, and optional `estimated_tokens` / `llm_used`.

### Admin (header `X-Admin-Key: $ADMIN_API_KEY`)

- `POST /api/admin/rebuild-index` — rebuild FAISS index in a background thread
- `POST /api/admin/run-evals` — start Ragas eval job; `GET /api/admin/eval-results/{job_id}` for status

## Evaluations

```bash
uv run python -m src.evals.eval_pipeline
```

Uses `data/eval_dataset.json` (≤15 rows), writes `data/eval_results/eval_<timestamp>.json`, and logs metric means via **structlog**.

## Tests

```bash
SKIP_PHOENIX=1 uv run pytest
```

Live Gemini end-to-end (slow, uses your quota):

```bash
RUN_GEMINI_E2E=1 GEMINI_API_KEY=... SKIP_PHOENIX=1 uv run pytest tests/test_pipeline.py::test_ask_valid_query -v
```

## Docker

```bash
docker compose up --build
```

API: `http://localhost:8000` · Phoenix: `http://localhost:${PHOENIX_PORT:-6006}`. The `./data` volume holds the vector index and eval outputs.

## Production features

- **Rate limiting**: 20 requests/minute per IP on `/api/ask` (slowapi)
- **Request tracing**: `X-Request-ID` on responses; Phoenix + OpenInference for LangChain spans
- **Structured logging**: structlog with query redaction after 50 characters
- **Eval pipeline**: Ragas (faithfulness, answer relevancy, context precision) with Gemini as judge
- **Fallback LLM**: Groq when Gemini fails
- **Citation-grounded answers**: numbered chunks with `source_file`, `page`, `ipc_section` metadata
- **Lazy loading**: embeddings and index load on first retrieval, not at import time
- **No pickle** for embeddings; index under `data/index/` (gitignored)
- **CORS**: `allow_credentials=False`; origins from `CORS_ORIGINS`
- **Timeouts**: `ASK_TIMEOUT_SECONDS` (default 30) wraps the async pipeline

## License

MIT — see [LICENSE](LICENSE).
