"""
Single source of truth for all configuration.
All values read from environment variables with documented defaults.
Import this module wherever config is needed — never call os.getenv directly elsewhere.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# LLM models
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# API keys
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
ADMIN_API_KEY: str | None = os.getenv("ADMIN_API_KEY")

# Retrieval
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K: int = int(os.getenv("TOP_K", "5"))
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))

# API behaviour
ASK_TIMEOUT_SECONDS: float = float(os.getenv("ASK_TIMEOUT_SECONDS", "30"))
RATE_LIMIT: str = os.getenv("RATE_LIMIT", "20/minute")
_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()]

# Observability
PHOENIX_PORT: int = int(os.getenv("PHOENIX_PORT", "6006"))
METRICS_MAXLEN: int = int(os.getenv("METRICS_MAXLEN", "5000"))
SKIP_PHOENIX: bool = os.getenv("SKIP_PHOENIX", "0").lower() in ("1", "true", "yes")
_phoenix_otlp_raw = os.getenv("PHOENIX_OTLP_ENDPOINT")
PHOENIX_OTLP_ENDPOINT: str = (
    _phoenix_otlp_raw.strip()
    if _phoenix_otlp_raw and _phoenix_otlp_raw.strip()
    else f"http://localhost:{PHOENIX_PORT}/v1/traces"
)

# Cache
CACHE_TTL: float = float(os.getenv("CACHE_TTL", "3600"))
CACHE_MAXSIZE: int = int(os.getenv("CACHE_MAXSIZE", "200"))

# Sessions
SESSION_TTL: float = float(os.getenv("SESSION_TTL", "3600"))
MAX_SESSION_MESSAGES: int = int(os.getenv("MAX_SESSION_MESSAGES", "10"))

# Evals
EVAL_DATASET_PATH: str = os.getenv("EVAL_DATASET_PATH", "data/eval_dataset.json")
MAX_EVAL_ROWS: int = int(os.getenv("MAX_EVAL_ROWS", "15"))

# Disclaimer
DISCLAIMER: str = (
    "This is not legal advice. "
    "Information is based on publicly available legal text. "
    "Consult a qualified lawyer for your specific situation."
)
