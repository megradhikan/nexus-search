import logging
from collections import defaultdict

import numpy as np

from nexus.db.connection import execute
from nexus.retrieval.bm25_index import search_bm25
from nexus.retrieval.dense_search import search_dense
from pipeline.embedder import embed_query

logger = logging.getLogger(__name__)

_chunk_cache: dict[str, dict] = {}


def load_chunk_cache() -> None:
    global _chunk_cache
    rows = execute(
        "SELECT chunk_id, doc_id, source, url, title, text FROM chunks WHERE embedding IS NOT NULL;"
    ) or []
    _chunk_cache = {
        row[0]: {
            "chunk_id": row[0],
            "doc_id": row[1],
            "source": row[2],
            "url": row[3],
            "title": row[4],
            "text": row[5],
        }
        for row in rows
    }
    logger.info(f"Chunk cache loaded: {len(_chunk_cache)} chunks.")


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[str, float]]],
    k: int = 60,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        for rank, (chunk_id, _) in enumerate(ranked, start=1):
            scores[chunk_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def hybrid_search(
    query: str,
    top_k: int = 10,
    source_filter: list[str] | None = None,
) -> list[dict]:
    bm25_results = search_bm25(query, top_k=50)
    query_embedding = embed_query(query)
    dense_results = search_dense(query_embedding, top_k=50, source_filter=source_filter)

    if source_filter:
        bm25_set = {cid for cid, _ in bm25_results}
        filtered_bm25 = []
        for chunk_id, score in bm25_results:
            meta = _chunk_cache.get(chunk_id)
            if meta and meta["source"] in source_filter:
                filtered_bm25.append((chunk_id, score))
        bm25_results = filtered_bm25

    bm25_ids = {cid for cid, _ in bm25_results}
    dense_ids = {cid for cid, _ in dense_results}
    fused = reciprocal_rank_fusion([bm25_results, dense_results])[:top_k]

    results = []
    for rank, (chunk_id, rrf_score) in enumerate(fused, start=1):
        meta = _chunk_cache.get(chunk_id)
        if not meta:
            rows = execute(
                "SELECT doc_id, source, url, title, text FROM chunks WHERE chunk_id = %s;",
                (chunk_id,),
            )
            if not rows:
                continue
            r = rows[0]
            meta = {"doc_id": r[0], "source": r[1], "url": r[2], "title": r[3], "text": r[4]}

        retrieval_sources = []
        if chunk_id in bm25_ids:
            retrieval_sources.append("bm25")
        if chunk_id in dense_ids:
            retrieval_sources.append("dense")

        results.append({
            "rank": rank,
            "chunk_id": chunk_id,
            "doc_id": meta["doc_id"],
            "title": meta["title"],
            "source": meta["source"],
            "url": meta["url"],
            "excerpt": meta["text"][:300],
            "rrf_score": rrf_score,
            "in_bm25": chunk_id in bm25_ids,
            "in_dense": chunk_id in dense_ids,
            "retrieval_sources": retrieval_sources,
        })
    return results
