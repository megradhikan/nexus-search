import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from api.main import app

FAKE_RESULTS = [
    {
        "rank": 1, "chunk_id": "c1", "doc_id": "d1", "title": "Doc 1",
        "source": "github", "url": "https://example.com/1",
        "excerpt": "some text", "rrf_score": 0.9,
        "in_bm25": True, "in_dense": False, "retrieval_sources": ["bm25"],
    },
    {
        "rank": 2, "chunk_id": "c2", "doc_id": "d2", "title": "Doc 2",
        "source": "notion", "url": "https://example.com/2",
        "excerpt": "other text", "rrf_score": 0.8,
        "in_bm25": False, "in_dense": True, "retrieval_sources": ["dense"],
    },
]


@pytest.fixture
def mock_startup():
    with patch("api.main.load_chunk_cache"), \
         patch("api.main.is_stale", return_value=False), \
         patch("api.main.load_index", return_value=True):
        yield


@pytest.mark.asyncio
async def test_search_returns_200(mock_startup):
    with patch("api.routes.search.hybrid_search", return_value=FAKE_RESULTS):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/search", json={"query": "test"})
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 2


@pytest.mark.asyncio
async def test_search_includes_latency_ms(mock_startup):
    with patch("api.routes.search.hybrid_search", return_value=FAKE_RESULTS):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/search", json={"query": "test"})
    assert "latency_ms" in resp.json()
    assert resp.json()["latency_ms"] > 0


@pytest.mark.asyncio
async def test_feedback_accepted(mock_startup):
    with patch("api.routes.search.insert_feedback"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/feedback", json={
                "query_text": "test", "doc_id": "d1",
                "rank_at_feedback": 1, "signal": "positive",
            })
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_endpoint(mock_startup):
    with patch("api.routes.health.execute", return_value=[(None,)]), \
         patch("api.routes.health.rrf_module._chunk_cache", {}), \
         patch("api.routes.health.bm25_index._bm25", None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_search_source_filter(mock_startup):
    with patch("api.routes.search.hybrid_search", return_value=[]) as mock_search:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/search", json={"query": "test", "sources": ["github"]})
    mock_search.assert_called_once_with("test", 10, ["github"])
