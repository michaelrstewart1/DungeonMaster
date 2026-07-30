"""Timing middleware: every response carries X-Process-Time for client-side
latency correlation (used by the playtest harness's analyzer)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_has_process_time_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/health")
    assert res.status_code == 200
    assert "x-process-time" in res.headers
    assert float(res.headers["x-process-time"]) >= 0
