# JusticeGuide — production RAG (IPC) + Next.js frontend

JusticeGuide is an IPC-focused RAG system with:
- Python API (FastAPI + LangChain + LlamaIndex + FAISS)
- Next.js frontend in `apps/web`
- Gemini primary model with Groq fallback
- Phoenix tracing and Ragas evaluation pipeline

## Architecture

```
                 +-----------------------+
                 |  Next.js app (web)    |
                 |  apps/web             |
                 +----------+------------+
                            |
                            v
                   POST /api/ask (FastAPI)
                            |
                            v
                +--------------------------+
                | query_enhancement (LCEL) |
                | Gemini / Groq            |
                +------------+-------------+
                             |
                             v
                +--------------------------+
                | retriever (lazy)         |
                | LlamaIndex + FAISS       |
                | dataset/.pdf/.md/.txt    |
                +------------+-------------+
                             |
                             v
                +--------------------------+
                | answer_generation (LCEL) |
                +------------+-------------+
                             |
                             v
                    JSON + citations
```

## Clean project structure

```
Justice-Guide/
├── apps/
│   └── web/                  # Next.js frontend
├── src/                      # FastAPI + RAG backend
├── dataset/
│   └── corpus/               # Seed legal corpus (.md/.txt)
├── data/
│   ├── eval_dataset.json
│   └── index/                # FAISS index (generated, gitignored)
└── tests/
```

## Prerequisites

- Python **3.11–3.13**
- [uv](https://docs.astral.sh/uv/) for Python dependencies
- Node.js 20+ for the Next.js frontend
- API keys: Gemini and optionally Groq

## Setup (Python backend with `uv`)

```bash
cd Justice-Guide
cp .env.example .env
uv sync --all-groups
```

## Data ingestion

The retriever now loads any of these file types from `dataset/` (recursively):
- `.pdf`
- `.md`
- `.txt`

The repo includes starter content under `dataset/corpus/`.
If no files exist, the backend falls back to an expanded built-in IPC sample set.

### Automated corpus import command

Use the ingestion CLI to import files in bulk and optionally rebuild the index:

```bash
# Import all supported files from a directory (recursive)
uv run python -m src.ingest --from-dir /path/to/legal-docs

# Import explicit files and rebuild index after copy
uv run python -m src.ingest ./notes/section302.md ./raw/ipc_chapter.pdf --rebuild-index
```

Optional flags:
- `--clear-destination`: wipe destination corpus directory before import
- `--dest`: custom destination directory (default `dataset/corpus`)
- `--dry-run`: preview actions without writing files

## Run backend API

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

- API health: `http://localhost:8000/api/health`
- Phoenix (optional): `http://127.0.0.1:6006`

## Run Next.js frontend

```bash
cd apps/web
npm install
npm run dev
```

Set API URL if backend is not on default host:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Default frontend URL: `http://localhost:3000`

## Core API endpoints

- `POST /api/ask` with `{"query":"..."}`
- `GET /api/debug/providers` (requires `X-Admin-Key`; live Gemini/Groq reachability check)
- `POST /api/admin/rebuild-index` (requires `X-Admin-Key`)
- `POST /api/admin/run-evals` (requires `X-Admin-Key`)
- `GET /api/admin/eval-results/{job_id}` (requires `X-Admin-Key`)

## Evaluations

```bash
uv run python -m src.evals.eval_pipeline
```

Uses `data/eval_dataset.json` and writes timestamped results to `data/eval_results/`.

## Tests

```bash
SKIP_PHOENIX=1 uv run pytest
```

## Docker (backend)

```bash
docker compose up --build
```

Backend API: `http://localhost:8000`

## License

MIT — see [LICENSE](LICENSE).
