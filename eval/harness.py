import json
import logging
from collections import defaultdict

import numpy as np
from sklearn.metrics import ndcg_score

from nexus.db.connection import execute

logger = logging.getLogger(__name__)


def load_judgments_from_feedback(min_positives: int = 1) -> dict[str, list[str]]:
    rows = execute(
        "SELECT query_text, doc_id FROM feedback WHERE signal = 'positive';"
    ) or []
    grouped: dict[str, list[str]] = defaultdict(list)
    for query_text, doc_id in rows:
        grouped[query_text].append(doc_id)
    return {q: docs for q, docs in grouped.items() if len(docs) >= min_positives}


def load_judgments_from_file(path: str) -> dict[str, list[str]]:
    with open(path) as f:
        return json.load(f)


def compute_mrr(
    results_by_query: dict[str, list[str]],
    judgments: dict[str, list[str]],
) -> float:
    reciprocal_ranks = []
    for query, relevant_ids in judgments.items():
        result_ids = results_by_query.get(query, [])
        rr = 0.0
        for rank, doc_id in enumerate(result_ids, start=1):
            if doc_id in relevant_ids:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)
    return float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0


def compute_ndcg_at_k(
    results_by_query: dict[str, list[str]],
    judgments: dict[str, list[str]],
    k: int = 5,
) -> float:
    ndcg_scores = []
    for query, relevant_ids in judgments.items():
        result_ids = results_by_query.get(query, [])[:k]
        if not result_ids:
            ndcg_scores.append(0.0)
            continue
        y_true = [[1 if doc_id in relevant_ids else 0 for doc_id in result_ids]]
        y_score = [[k - i for i in range(len(result_ids))]]
        if sum(y_true[0]) == 0:
            ndcg_scores.append(0.0)
        else:
            ndcg_scores.append(ndcg_score(y_true, y_score, k=k))
    return float(np.mean(ndcg_scores)) if ndcg_scores else 0.0


def run_eval(
    judgments: dict[str, list[str]],
    top_k: int = 10,
    source_filter: list[str] | None = None,
) -> dict:
    from nexus.retrieval.rrf import hybrid_search
    from nexus.retrieval.bm25_index import search_bm25
    from nexus.retrieval.dense_search import search_dense
    from pipeline.embedder import embed_query
    from nexus.db.connection import execute as db_execute

    hybrid_results: dict[str, list[str]] = {}
    bm25_results: dict[str, list[str]] = {}
    dense_results: dict[str, list[str]] = {}

    def chunk_ids_to_doc_ids(chunk_id_scores: list[tuple[str, float]]) -> list[str]:
        seen = []
        for chunk_id, _ in chunk_id_scores:
            rows = db_execute("SELECT doc_id FROM chunks WHERE chunk_id = %s;", (chunk_id,))
            if rows and rows[0][0] not in seen:
                seen.append(rows[0][0])
        return seen

    for query in judgments:
        h = hybrid_search(query, top_k, source_filter)
        hybrid_results[query] = [r["doc_id"] for r in h]

        bm25 = search_bm25(query, top_k)
        bm25_results[query] = chunk_ids_to_doc_ids(bm25)

        emb = embed_query(query)
        dense = search_dense(emb, top_k, source_filter)
        dense_results[query] = chunk_ids_to_doc_ids(dense)

    n = len(judgments)
    return {
        "hybrid": {
            "mrr": compute_mrr(hybrid_results, judgments),
            "ndcg_at_5": compute_ndcg_at_k(hybrid_results, judgments, k=5),
            "n_queries": n,
        },
        "bm25_only": {
            "mrr": compute_mrr(bm25_results, judgments),
            "ndcg_at_5": compute_ndcg_at_k(bm25_results, judgments, k=5),
        },
        "dense_only": {
            "mrr": compute_mrr(dense_results, judgments),
            "ndcg_at_5": compute_ndcg_at_k(dense_results, judgments, k=5),
        },
    }
