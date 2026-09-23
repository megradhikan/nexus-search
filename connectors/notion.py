import time
import logging
from datetime import datetime, timezone

from notion_client import Client

from connectors.base import BaseConnector
from nexus.models import RawDocument, NormalizedDocument

logger = logging.getLogger(__name__)

BLOCK_TYPES = {
    "paragraph", "heading_1", "heading_2", "heading_3",
    "bulleted_list_item", "numbered_list_item", "code", "quote", "callout", "toggle",
}


class NotionConnector(BaseConnector):
    def __init__(self, token: str):
        self._client = Client(auth=token)

    def fetch_all(self) -> list[NormalizedDocument]:
        return self.fetch_updated_since(datetime(2000, 1, 1, tzinfo=timezone.utc))

    def fetch_updated_since(self, since: datetime) -> list[NormalizedDocument]:
        docs = []
        results = []
        cursor = None
        while True:
            kwargs = {"filter": {"property": "object", "value": "page"}}
            if cursor:
                kwargs["start_cursor"] = cursor
            resp = self._client.search(**kwargs)
            results.extend(resp.get("results", []))
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")

        for page in results:
            last_edited = page.get("last_edited_time", "")
            try:
                edited_dt = datetime.fromisoformat(last_edited.replace("Z", "+00:00"))
            except ValueError:
                continue
            if edited_dt < since:
                continue

            title = self._extract_title(page)
            text = self._extract_text(page["id"])
            raw = RawDocument(
                source="notion",
                source_native_id=page["id"],
                doc_type="notion_page",
                url=page.get("url", ""),
                title=title,
                raw_text=text,
                updated_at=edited_dt,
                created_at=None,
                metadata={
                    "parent_id": page.get("parent"),
                    "database_id": page.get("parent", {}).get("database_id"),
                    "author": page.get("created_by", {}).get("id"),
                },
            )
            docs.append(self.normalize(raw))
        return docs

    def _extract_title(self, page: dict) -> str:
        props = page.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "title":
                parts = prop.get("title", [])
                return "".join(p.get("plain_text", "") for p in parts)
        return ""

    def _extract_text(self, block_id: str) -> str:
        time.sleep(0.35)
        resp = self._client.blocks.children.list(block_id=block_id)
        parts = []
        for block in resp.get("results", []):
            btype = block.get("type")
            if btype in BLOCK_TYPES:
                rich = block.get(btype, {}).get("rich_text", [])
                text = "".join(r.get("plain_text", "") for r in rich)
                parts.append(text)
            if block.get("has_children"):
                parts.append(self._extract_text(block["id"]))
        return "\n".join(parts)
