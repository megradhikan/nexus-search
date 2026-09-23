import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def job_connector_sync() -> dict:
    from nexus.config import get_settings
    from nexus.db.queries import upsert_document, upsert_sync_state, get_sync_state

    settings = get_settings()
    total = 0

    for name in ["github", "notion"]:
        token = getattr(settings, f"{name}_token", "")
        if not token:
            logger.info(f"Skipping {name}: no token configured.")
            continue
        try:
            state = get_sync_state(name)
            since = state["last_synced_at"] if state else datetime(1970, 1, 1, tzinfo=timezone.utc)

            if name == "github":
                from connectors.github import GitHubConnector
                repos = getattr(settings, "github_repos", [])
                connector = GitHubConnector(token, repos)
            else:
                from connectors.notion import NotionConnector
                connector = NotionConnector(token)

            docs = connector.fetch_updated_since(since)
            for doc in docs:
                upsert_document(doc)
            upsert_sync_state(name, datetime.now(timezone.utc), "success", len(docs), None)
            logger.info(f"Synced {len(docs)} docs from {name}")
            total += len(docs)
        except Exception as e:
            logger.error(f"Sync failed for {name}: {e}")
            upsert_sync_state(name, None, "failed", 0, str(e))

    return {"synced": total}


def job_embedding_pipeline() -> dict:
    from pipeline.runner import run_embedding_pipeline
    count = run_embedding_pipeline()
    return {"embedded": count}


def job_bm25_rebuild() -> dict:
    from nexus.retrieval.bm25_index import is_stale, build_index
    from nexus.retrieval.rrf import load_chunk_cache

    stale = is_stale()
    if stale:
        build_index()
        load_chunk_cache()
        logger.info("BM25 index rebuilt.")
    else:
        logger.info("BM25 index is current, skipping rebuild.")
    return {"rebuilt": stale}
