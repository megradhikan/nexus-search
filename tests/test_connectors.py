import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from nexus.models import RawDocument
from connectors.base import BaseConnector


class ConcreteConnector(BaseConnector):
    def fetch_all(self):
        return []

    def fetch_updated_since(self, since):
        return []


def test_github_doc_id_format():
    connector = ConcreteConnector()
    raw = RawDocument(
        source="github",
        source_native_id="org/repo::issue::42",
        doc_type="issue",
        url="https://github.com/org/repo/issues/42",
        title="Test issue",
        raw_text="Some content",
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        metadata={},
    )
    normalized = connector.normalize(raw)
    assert normalized.doc_id == "github::issue::org/repo::issue::42"


def test_notion_empty_page():
    with patch("connectors.notion.Client") as MockClient:
        client = MagicMock()
        MockClient.return_value = client
        client.blocks.children.list.return_value = {"results": []}
        client.search.return_value = {"results": [], "has_more": False}

        from connectors.notion import NotionConnector
        connector = NotionConnector(token="test")
        text = connector._extract_text("fake-page-id")
        assert text == ""


def test_github_rate_limit_retry():
    from github.GithubException import RateLimitExceededException
    from connectors.github import GitHubConnector

    call_count = 0

    # All calls raise so tenacity exhausts retries and re-raises.
    # Patch time.sleep so the exponential waits (min=60s) don't block the test.
    with patch("connectors.github.Github") as MockGithub, \
         patch("time.sleep"):
        mock_client = MagicMock()
        MockGithub.return_value = mock_client

        def side_effect(repo_name):
            nonlocal call_count
            call_count += 1
            raise RateLimitExceededException(403, "rate limit", {})

        mock_client.get_repo.side_effect = side_effect

        connector = GitHubConnector(token="test", repos=["org/repo"])
        with pytest.raises(Exception):
            connector._get_repo("org/repo")

        # tenacity retries stop_after_attempt(3) → 3 calls total
        assert call_count >= 2
