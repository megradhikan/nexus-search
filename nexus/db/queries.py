import json
from datetime import datetime
from typing import Optional

from psycopg2.extras import execute_values

from nexus.db.connection import get_conn, execute
from nexus.models import NormalizedDocument, Chunk


def upsert_document(doc: NormalizedDocument) -> None:
    sql = """
        INSERT INTO documents
            (doc_id, source, doc_type, url, title, raw_text, author,
             created_at, updated_at, metadata, embedded_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)
        ON CONFLICT (doc_id) DO UPDATE SET
            raw_text = EXCLUDED.raw_text,
            title = EXCLUDED.title,
            updated_at = EXCLUDED.updated_at,
            embedded_at = NULL,
            metadata = EXCLUDED.metadata
        WHERE EXCLUDED.updated_at > documents.updated_at;
    """
    author = doc.metadata.get("author")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                doc.doc_id, doc.source, doc.doc_type, doc.url, doc.title,
                doc.raw_text, author, doc.created_at, doc.updated_at,
                json.dumps(doc.metadata),
            ))


def upsert_chunks(chunks: list[Chunk]) -> None:
    if not chunks:
        return
    sql = """
        INSERT INTO chunks
            (chunk_id, doc_id, position, text, token_count, embedding,
             embedded_at, source, url, title)
        VALUES %s
        ON CONFLICT (chunk_id) DO UPDATE SET
            text = EXCLUDED.text,
            token_count = EXCLUDED.token_count,
            embedding = EXCLUDED.embedding,
            embedded_at = EXCLUDED.embedded_at;
    """
    rows = []
    for c in chunks:
        emb = c.embedding.tolist() if c.embedding is not None else None
        rows.append((
            c.chunk_id, c.doc_id, c.position, c.text, c.token_count,
            emb, datetime.utcnow() if emb else None,
            c.source, c.url, c.title,
        ))
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, rows)


def get_unembedded_documents() -> list[NormalizedDocument]:
    sql = """
        SELECT doc_id, source, doc_type, url, title, raw_text,
               created_at, updated_at, metadata
        FROM documents
        WHERE embedded_at IS NULL OR embedded_at < updated_at;
    """
    rows = execute(sql) or []
    docs = []
    for row in rows:
        doc_id, source, doc_type, url, title, raw_text, created_at, updated_at, metadata = row
        doc = NormalizedDocument(
            source=source, source_native_id="", doc_type=doc_type, url=url,
            title=title, raw_text=raw_text, created_at=created_at,
            updated_at=updated_at, metadata=metadata or {}, doc_id=doc_id,
        )
        docs.append(doc)
    return docs


def get_all_chunks_text() -> list[tuple[str, str]]:
    rows = execute("SELECT chunk_id, text FROM chunks;") or []
    return [(r[0], r[1]) for r in rows]


def mark_document_embedded(doc_id: str) -> None:
    execute("UPDATE documents SET embedded_at = NOW() WHERE doc_id = %s;", (doc_id,))


def upsert_sync_state(
    connector_name: str,
    last_synced_at: Optional[datetime],
    status: str,
    docs_synced: int,
    error: Optional[str],
) -> None:
    sql = """
        INSERT INTO sync_state
            (connector_name, last_synced_at, last_run_at, last_run_status,
             docs_synced, error_message)
        VALUES (%s, %s, NOW(), %s, %s, %s)
        ON CONFLICT (connector_name) DO UPDATE SET
            last_synced_at = EXCLUDED.last_synced_at,
            last_run_at = NOW(),
            last_run_status = EXCLUDED.last_run_status,
            docs_synced = EXCLUDED.docs_synced,
            error_message = EXCLUDED.error_message;
    """
    execute(sql, (connector_name, last_synced_at, status, docs_synced, error))


def get_sync_state(connector_name: str) -> dict | None:
    rows = execute(
        "SELECT connector_name, last_synced_at, last_run_at, last_run_status, "
        "docs_synced, error_message FROM sync_state WHERE connector_name = %s;",
        (connector_name,),
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "connector_name": r[0],
        "last_synced_at": r[1],
        "last_run_at": r[2],
        "last_run_status": r[3],
        "docs_synced": r[4],
        "error_message": r[5],
    }


def insert_feedback(
    query_text: str,
    doc_id: str,
    chunk_id: Optional[str],
    rank: int,
    signal: str,
) -> None:
    sql = """
        INSERT INTO feedback (query_text, doc_id, chunk_id, rank_at_feedback, signal)
        VALUES (%s, %s, %s, %s, %s);
    """
    execute(sql, (query_text, doc_id, chunk_id, rank, signal))
