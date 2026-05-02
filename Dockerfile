FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
ENV UV_PRERELEASE=allow

# Lockfile must be copied before sync so the image matches the repo and `uv run`
# does not reinstall hundreds of wheels on container start (Render port scan timeout).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000 6006

# Render (and similar hosts) set PORT; default 8000 for local/docker compose.
CMD ["sh", "-c", "uv run uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
