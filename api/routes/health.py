from fastapi import APIRouter
from nexus.db.connection import execute
from nexus.retrieval import rrf as rrf_module
from nexus.retrieval import bm25_index

router = APIRouter()


@router.get("/health")
def health():
    rows = execute("SELECT MAX(embedded_at) FROM chunks;")
    max_embedded = rows[0][0] if rows and rows[0][0] else None

    if max_embedded:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if max_embedded.tzinfo is None:
            from datetime import timezone as tz
            max_embedded = max_embedded.replace(tzinfo=tz.utc)
        lag_minutes = (now - max_embedded).total_seconds() / 60
    else:
        lag_minutes = 0.0

    return {
        "status": "ok",
        "chunks_indexed": len(rrf_module._chunk_cache),
        "bm25_index_loaded": bm25_index._bm25 is not None,
        "freshness_lag_minutes": lag_minutes,
    }
