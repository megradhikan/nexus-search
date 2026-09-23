import logging
import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nexus.db.queries import insert_feedback
from nexus.retrieval import rrf as rrf_module
from nexus.retrieval.rrf import hybrid_search, _chunk_cache

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)
    sources: Optional[list[str]] = None
    debug: bool = False


class SearchResult(BaseModel):
    rank: int
    doc_id: str
    title: Optional[str]
    source: str
    url: str
    excerpt: str
    rrf_score: float
    retrieval_sources: list[str]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    latency_ms: float
    total_chunks_indexed: int
    timings: Optional[dict] = None


class FeedbackRequest(BaseModel):
    query_text: str
    doc_id: str
    chunk_id: Optional[str] = None
    rank_at_feedback: int
    signal: str


@router.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    t_start = time.perf_counter()
    timings = {} if req.debug else None

    if req.debug:
        t0 = time.perf_counter()

    raw_results = hybrid_search(req.query, req.top_k, req.sources)

    if req.debug:
        timings["hybrid_search_ms"] = (time.perf_counter() - t0) * 1000

    results = [SearchResult(**{k: v for k, v in r.items() if k in SearchResult.model_fields}) for r in raw_results]
    latency_ms = (time.perf_counter() - t_start) * 1000
    logger.info(f"Query: '{req.query}' | Results: {len(results)} | {latency_ms:.1f}ms")

    return SearchResponse(
        query=req.query,
        results=results,
        latency_ms=latency_ms,
        total_chunks_indexed=len(rrf_module._chunk_cache),
        timings=timings,
    )


@router.post("/feedback")
def feedback(req: FeedbackRequest):
    insert_feedback(req.query_text, req.doc_id, req.chunk_id, req.rank_at_feedback, req.signal)
    return {"status": "ok"}
