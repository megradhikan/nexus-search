from contextlib import contextmanager
from psycopg2 import pool
from psycopg2.extras import execute_values
from nexus.config import get_settings

_pool: pool.ThreadedConnectionPool | None = None


def get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = pool.ThreadedConnectionPool(2, 10, settings.database_url)
    return _pool


@contextmanager
def get_conn():
    p = get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def execute(sql: str, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            try:
                return cur.fetchall()
            except Exception:
                return None


def execute_many(sql: str, params_list: list):
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, params_list)
