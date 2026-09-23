import numpy as np
from sentence_transformers import SentenceTransformer

from nexus.models import Chunk

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def embed_chunks(chunks: list[Chunk]) -> list[Chunk]:
    if not chunks:
        return chunks
    model = get_model()
    texts = [c.text for c in chunks]
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    for chunk, emb in zip(chunks, embeddings):
        chunk.embedding = emb
    return chunks


def embed_query(query: str) -> np.ndarray:
    model = get_model()
    return model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
