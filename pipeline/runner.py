import logging

from nexus.db.queries import get_unembedded_documents, upsert_chunks, mark_document_embedded
from pipeline.chunker import chunk_document
from pipeline.embedder import embed_chunks

logger = logging.getLogger(__name__)


def run_embedding_pipeline() -> int:
    docs = get_unembedded_documents()
    if not docs:
        logger.info("No documents to embed.")
        return 0

    embedded_count = 0
    for doc in docs:
        chunks = chunk_document(doc)
        if not chunks:
            logger.warning(f"No chunks for {doc.doc_id}, skipping.")
            continue
        embed_chunks(chunks)
        upsert_chunks(chunks)
        mark_document_embedded(doc.doc_id)
        logger.info(f"Embedded {len(chunks)} chunks for {doc.doc_id}")
        embedded_count += 1

    return embedded_count


if __name__ == "__main__":
    count = run_embedding_pipeline()
    print(f"Embedded {count} documents.")
