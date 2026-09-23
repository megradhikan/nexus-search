import os
import pytest
from unittest.mock import patch, MagicMock


def test_job_connector_sync_skips_missing_token():
    # Patch at the source module since jobs.py imports lazily
    with patch("nexus.config.get_settings") as mock_settings:
        settings = MagicMock()
        settings.github_token = ""
        settings.notion_token = ""
        mock_settings.return_value = settings

        with patch("connectors.github.GitHubConnector") as mock_gh:
            from scheduler.jobs import job_connector_sync
            result = job_connector_sync()
            mock_gh.assert_not_called()
            assert result["synced"] == 0


def test_job_embedding_pipeline_calls_runner():
    # Patch at the actual module where it's defined
    with patch("pipeline.runner.run_embedding_pipeline", return_value=5):
        from scheduler.jobs import job_embedding_pipeline
        result = job_embedding_pipeline()
        assert result == {"embedded": 5}


def test_job_bm25_rebuild_skips_if_current():
    with patch("nexus.retrieval.bm25_index.is_stale", return_value=False), \
         patch("nexus.retrieval.bm25_index.build_index") as mock_build:
        from scheduler.jobs import job_bm25_rebuild
        result = job_bm25_rebuild()
        mock_build.assert_not_called()
        assert result == {"rebuilt": False}
