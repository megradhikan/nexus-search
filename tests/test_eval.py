import pytest
from eval.harness import compute_mrr, compute_ndcg_at_k


def test_mrr_perfect():
    results = {"q1": ["d1", "d2"]}
    judgments = {"q1": ["d1"]}
    assert compute_mrr(results, judgments) == 1.0


def test_mrr_rank_two():
    results = {"q1": ["d2", "d1"]}
    judgments = {"q1": ["d1"]}
    assert compute_mrr(results, judgments) == 0.5


def test_mrr_not_found():
    results = {"q1": ["d2", "d3"]}
    judgments = {"q1": ["d1"]}
    assert compute_mrr(results, judgments) == 0.0


def test_ndcg_perfect():
    results = {"q1": ["d1", "d2", "d3", "d4", "d5"]}
    judgments = {"q1": ["d1", "d2", "d3", "d4", "d5"]}
    score = compute_ndcg_at_k(results, judgments, k=5)
    assert abs(score - 1.0) < 1e-6
