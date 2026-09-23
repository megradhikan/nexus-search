import logging
import pickle
from pathlib import Path

import nltk
from rank_bm25 import BM25Okapi

from nexus.db.connection import execute
from nexus.db.queries import get_all_chunks_text

logger = logging.getLogger(__name__)

_bm25: BM25Okapi | None = None
_chunk_ids: list[str] = []
_index_path = Path("bm25_index.pkl")

try:
    _stopwords = set(nltk.corpus.stopwords.words("english"))
except LookupError:
    nltk.download("stopwords", quiet=True)
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
    _stopwords = set(nltk.corpus.stopwords.words("english"))


def tokenize(text: str) -> list[str]:
    tokens = nltk.word_tokenize(text.lower())
    return [t for t in tokens if t.isalpha() and t not in _stopwords]


def build_index() -> None:
    global _bm25, _chunk_ids
    rows = get_all_chunks_text()
    if not rows:
        logger.info("BM25 index skipped: no chunks in database yet.")
        return
    _chunk_ids = [r[0] for r in rows]
    corpus = [tokenize(r[1]) for r in rows]
    _bm25 = BM25Okapi(corpus)
    with open(_index_path, "wb") as f:
        pickle.dump((_bm25, _chunk_ids), f)
    logger.info(f"BM25 index built: {len(_chunk_ids)} chunks.")


def load_index() -> bool:
    global _bm25, _chunk_ids
    if not _index_path.exists():
        return False
    with open(_index_path, "rb") as f:
        _bm25, _chunk_ids = pickle.load(f)
    return True


def is_stale() -> bool:
    if not _index_path.exists():
        return True
    rows = execute("SELECT MAX(embedded_at) FROM chunks;")
    if not rows or rows[0][0] is None:
        return False
    max_embedded = rows[0][0].timestamp()
    index_mtime = _index_path.stat().st_mtime
    return max_embedded > index_mtime


def search_bm25(query: str, top_k: int = 50) -> list[tuple[str, float]]:
    global _bm25, _chunk_ids
    if _bm25 is None:
        if not load_index():
            return []
    if not _chunk_ids:
        return []
    tokens = tokenize(query)
    scores = _bm25.get_scores(tokens)
    ranked = sorted(zip(_chunk_ids, scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
