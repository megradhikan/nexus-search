import numpy as np
import pytest
from datetime import datetime, timezone

from nexus.models import NormalizedDocument, Chunk
from pipeline.chunker import chunk_document
from pipeline.embedder import embed_chunks, embed_query

LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris. "
) * 20


def make_doc(text: str) -> NormalizedDocument:
    return NormalizedDocument(
        source="test",
        source_native_id="1",
        doc_type="issue",
        url="https://example.com",
        title="Test",
        raw_text=text,
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        metadata={},
        doc_id="test::issue::1",
    )


def test_chunker_basic():
    doc = make_doc(LOREM)
    chunks = chunk_document(doc)
    assert len(chunks) >= 2
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
    assert all(c.token_count <= 512 for c in chunks)


def test_chunker_short_doc():
    doc = make_doc("This is a short document with few words.")
    chunks = chunk_document(doc)
    assert len(chunks) == 1


def test_embedder_shape():
    chunks = [
        Chunk(chunk_id=f"c{i}", doc_id="d1", position=i, text=f"Sample text number {i}",
              token_count=5, source="test", url="https://example.com")
        for i in range(3)
    ]
    result = embed_chunks(chunks)
    for c in result:
        assert c.embedding is not None
        assert c.embedding.shape == (384,)
        assert abs(np.linalg.norm(c.embedding) - 1.0) < 1e-5


def test_embed_query_shape():
    emb = embed_query("test query")
    assert emb.shape == (384,)
