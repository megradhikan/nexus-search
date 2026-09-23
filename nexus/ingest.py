import logging
from datetime import datetime, timezone

from nexus.config import get_settings
from nexus.db.queries import upsert_document, upsert_sync_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_ingest():
    settings = get_settings()
    connectors = {}

    if settings.github_token:
        from connectors.github import GitHubConnector
        repos = settings.github_repos if hasattr(settings, "github_repos") else []
        connectors["github"] = GitHubConnector(settings.github_token, repos)

    if settings.notion_token:
        from connectors.notion import NotionConnector
        connectors["notion"] = NotionConnector(settings.notion_token)

    for name, connector in connectors.items():
        try:
            docs = connector.fetch_all()
            for doc in docs:
                upsert_document(doc)
            logger.info(f"Ingested {len(docs)} documents from {name}")
            upsert_sync_state(name, datetime.now(timezone.utc), "success", len(docs), None)
        except Exception as e:
            logger.error(f"Error ingesting from {name}: {e}")
            upsert_sync_state(name, None, "failed", 0, str(e))


if __name__ == "__main__":
    run_ingest()
