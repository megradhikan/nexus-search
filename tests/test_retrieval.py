import pytest
from nexus.retrieval.rrf import reciprocal_rank_fusion
from nexus.retrieval.bm25_index import tokenize


def test_rrf_single_list():
    results = reciprocal_rank_fusion([[("a", 1.0), ("b", 0.9), ("c", 0.8)]])
    ids = [r[0] for r in results]
    assert ids == ["a", "b", "c"]
    assert abs(results[0][1] - 1 / (60 + 1)) < 1e-9


def test_rrf_two_lists_fusion():
    list1 = [("a", 1.0), ("b", 0.9)]
    list2 = [("c", 1.0), ("d", 0.9), ("a", 0.8)]
    results = dict(reciprocal_rank_fusion([list1, list2]))
    # "a" is rank 1 in list1, rank 3 in list2: 1/61 + 1/63
    # "b" is rank 2 in list1 only: 1/62
    assert results["a"] > results["b"]


def test_rrf_empty_list():
    results = reciprocal_rank_fusion([[], [("x", 1.0), ("y", 0.5)]])
    ids = [r[0] for r in results]
    assert "x" in ids
    assert "y" in ids


def test_bm25_tokenize():
    tokens = tokenize("The quick brown fox")
    assert "the" not in tokens
    assert "quick" in tokens
    assert "brown" in tokens
    assert "fox" in tokens
