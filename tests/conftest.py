import os

# Must run before any `src` import so `src.config` picks up test defaults.
os.environ.setdefault("SKIP_PHOENIX", "1")
os.environ.setdefault("ASK_TIMEOUT_SECONDS", "120")
os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")

import pytest


@pytest.fixture(scope="session", autouse=True)
def _test_env():
    pass


@pytest.fixture
async def async_client():
    from asgi_lifespan import LifespanManager
    from httpx import ASGITransport, AsyncClient

    from src.main import app

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
