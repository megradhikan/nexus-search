import logging
from datetime import datetime, timezone

from github import Github
from github.GithubException import RateLimitExceededException
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from connectors.base import BaseConnector
from nexus.models import RawDocument, NormalizedDocument

logger = logging.getLogger(__name__)


class GitHubConnector(BaseConnector):
    def __init__(self, token: str, repos: list[str]):
        self._client = Github(token)
        self._repos = repos

    def fetch_all(self) -> list[NormalizedDocument]:
        return self.fetch_updated_since(datetime(2000, 1, 1, tzinfo=timezone.utc))

    def fetch_updated_since(self, since: datetime) -> list[NormalizedDocument]:
        docs = []
        for repo_name in self._repos:
            repo = self._get_repo(repo_name)
            docs.extend(self._fetch_issues(repo, since))
            docs.extend(self._fetch_pulls(repo, since))
            docs.extend(self._fetch_markdown_files(repo, since))
        return docs

    @retry(
        retry=retry_if_exception_type(RateLimitExceededException),
        wait=wait_exponential(min=60, max=300),
        stop=stop_after_attempt(3),
    )
    def _get_repo(self, repo_name: str):
        return self._client.get_repo(repo_name)

    def _fetch_issues(self, repo, since: datetime) -> list[NormalizedDocument]:
        docs = []
        for issue in repo.get_issues(state="all", since=since):
            text = f"{issue.title}\n\n{issue.body or ''}"
            for comment in issue.get_comments():
                text += f"\n---\n{comment.body}"
            if not text.strip():
                continue
            raw = RawDocument(
                source="github",
                source_native_id=f"{repo.full_name}::issue::{issue.number}",
                doc_type="issue",
                url=issue.html_url,
                title=issue.title,
                raw_text=text,
                created_at=issue.created_at.replace(tzinfo=timezone.utc) if issue.created_at else None,
                updated_at=issue.updated_at.replace(tzinfo=timezone.utc),
                metadata={
                    "repo": repo.full_name,
                    "number": issue.number,
                    "state": issue.state,
                    "labels": [l.name for l in issue.labels],
                    "author": issue.user.login,
                },
            )
            docs.append(self.normalize(raw))
        return docs

    def _fetch_pulls(self, repo, since: datetime) -> list[NormalizedDocument]:
        docs = []
        for pr in repo.get_pulls(state="all", sort="updated", direction="desc"):
            if pr.updated_at.replace(tzinfo=timezone.utc) < since:
                break
            text = f"{pr.title}\n\n{pr.body or ''}"
            for comment in pr.get_review_comments():
                text += f"\n---\n{comment.body}"
            if not text.strip():
                continue
            raw = RawDocument(
                source="github",
                source_native_id=f"{repo.full_name}::pr::{pr.number}",
                doc_type="pull_request",
                url=pr.html_url,
                title=pr.title,
                raw_text=text,
                created_at=pr.created_at.replace(tzinfo=timezone.utc) if pr.created_at else None,
                updated_at=pr.updated_at.replace(tzinfo=timezone.utc),
                metadata={
                    "repo": repo.full_name,
                    "number": pr.number,
                    "state": pr.state,
                    "base_branch": pr.base.ref,
                    "labels": [l.name for l in pr.labels],
                },
            )
            docs.append(self.normalize(raw))
        return docs

    def _fetch_markdown_files(self, repo, since: datetime) -> list[NormalizedDocument]:
        docs = []
        contents = self._get_all_contents(repo, "")
        for content in contents:
            if not content.path.endswith(".md"):
                continue
            commits = list(repo.get_commits(path=content.path))
            if commits:
                last_commit_date = commits[0].commit.author.date.replace(tzinfo=timezone.utc)
                if last_commit_date < since:
                    continue
            text = content.decoded_content.decode("utf-8", errors="ignore")
            if not text.strip():
                continue
            raw = RawDocument(
                source="github",
                source_native_id=f"{repo.full_name}::md::{content.path}",
                doc_type="markdown_file",
                url=content.html_url,
                title=content.path,
                raw_text=text,
                updated_at=commits[0].commit.author.date.replace(tzinfo=timezone.utc) if commits else datetime.utcnow().replace(tzinfo=timezone.utc),
                metadata={"repo": repo.full_name, "path": content.path},
            )
            docs.append(self.normalize(raw))
        return docs

    def _get_all_contents(self, repo, path: str):
        items = []
        for content in repo.get_contents(path):
            if content.type == "dir":
                items.extend(self._get_all_contents(repo, content.path))
            else:
                items.append(content)
        return items
