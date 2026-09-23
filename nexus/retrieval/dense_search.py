import numpy as np
from nexus.db.connection import get_conn


def search_dense(
    query_embedding: np.ndarray,
    top_k: int = 50,
    source_filter: list[str] | None = None,
) -> list[tuple[str, float]]:
    vec = query_embedding.tolist()
    with get_conn() as conn:
        with conn.cursor() as cur:
            if source_filter:
                sql = """
                    SELECT chunk_id, 1 - (embedding <=> %s::vector) AS score
                    FROM chunks
                    WHERE embedding IS NOT NULL AND source = ANY(%s)
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """
                cur.execute(sql, (vec, source_filter, vec, top_k))
            else:
                sql = """
                    SELECT chunk_id, 1 - (embedding <=> %s::vector) AS score
                    FROM chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """
                cur.execute(sql, (vec, vec, top_k))
            return [(row[0], float(row[1])) for row in cur.fetchall()]
