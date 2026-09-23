from nexus.db.connection import get_conn


DDL = [
    "CREATE EXTENSION IF NOT EXISTS vector;",

    """
    CREATE TABLE IF NOT EXISTS documents (
        doc_id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        doc_type TEXT NOT NULL,
        url TEXT NOT NULL,
        title TEXT,
        raw_text TEXT NOT NULL,
        author TEXT,
        created_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ NOT NULL,
        indexed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        embedded_at TIMESTAMPTZ,
        metadata JSONB
    );
    """,

    "CREATE INDEX IF NOT EXISTS idx_documents_source ON documents (source);",
    "CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents (updated_at);",
    "CREATE INDEX IF NOT EXISTS idx_documents_unembedded ON documents (embedded_at) WHERE embedded_at IS NULL;",

    """
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        doc_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        text TEXT NOT NULL,
        token_count INTEGER NOT NULL,
        embedding vector(384),
        embedded_at TIMESTAMPTZ,
        source TEXT NOT NULL,
        url TEXT NOT NULL,
        title TEXT
    );
    """,

    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks (doc_id);",
    # Post-bulk-ingest: CREATE INDEX idx_chunks_embedding_ivfflat ON chunks
    # USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

    """
    CREATE TABLE IF NOT EXISTS sync_state (
        connector_name TEXT PRIMARY KEY,
        last_synced_at TIMESTAMPTZ,
        last_run_at TIMESTAMPTZ,
        last_run_status TEXT,
        docs_synced INTEGER DEFAULT 0,
        error_message TEXT
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS feedback (
        feedback_id SERIAL PRIMARY KEY,
        query_text TEXT NOT NULL,
        doc_id TEXT NOT NULL,
        chunk_id TEXT,
        rank_at_feedback INTEGER NOT NULL,
        signal TEXT NOT NULL CHECK (signal IN ('positive', 'negative')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,

    "CREATE INDEX IF NOT EXISTS idx_feedback_query_text ON feedback (query_text);",
]


def run_migrations():
    with get_conn() as conn:
        with conn.cursor() as cur:
            for stmt in DDL:
                cur.execute(stmt)
    print("Migration complete.")


if __name__ == "__main__":
    run_migrations()
