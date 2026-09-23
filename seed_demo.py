"""Seed the database with synthetic demo data so the app can be tested end-to-end."""
from datetime import datetime, timezone
from nexus.models import NormalizedDocument
from nexus.db.queries import upsert_document
from pipeline.chunker import chunk_document
from pipeline.embedder import embed_chunks
from nexus.db.queries import upsert_chunks, mark_document_embedded

DOCS = [
    NormalizedDocument(
        source="github", source_native_id="acme/backend::issue::101",
        doc_type="issue", url="https://github.com/acme/backend/issues/101",
        title="Retry logic with exponential backoff for API calls",
        raw_text=(
            "Retry logic with exponential backoff for API calls\n\n"
            "We need to add retry logic to our HTTP client. Currently when an external API "
            "returns a 503 or times out, we fail immediately. Proposal: use tenacity with "
            "exponential backoff starting at 1 second, max 30 seconds, stop after 5 attempts. "
            "We should also add jitter to prevent thundering herd problems.\n\n"
            "---\nAgreed. Also make sure we log each retry attempt with the status code and "
            "elapsed time so we can monitor retry rates in Datadog.\n"
            "---\nImplemented in PR #204. Used tenacity with wait_exponential(min=1, max=30) "
            "and added structured logging for each retry. Tests cover 503, timeout, and "
            "connection reset scenarios."
        ),
        updated_at=datetime(2024, 3, 15, tzinfo=timezone.utc),
        metadata={"repo": "acme/backend", "number": 101, "state": "closed",
                  "labels": ["enhancement", "reliability"]},
        doc_id="github::issue::acme/backend::issue::101",
    ),
    NormalizedDocument(
        source="github", source_native_id="acme/backend::pr::204",
        doc_type="pull_request", url="https://github.com/acme/backend/pull/204",
        title="Add exponential backoff retry to HTTP client",
        raw_text=(
            "Add exponential backoff retry to HTTP client\n\n"
            "Closes #101. This PR wraps our httpx client calls with tenacity retry logic. "
            "Configuration:\n- wait_exponential(multiplier=1, min=1, max=30)\n"
            "- stop_after_attempt(5)\n- retry_if_exception_type for httpx.TimeoutException "
            "and httpx.HTTPStatusError (only 5xx codes)\n\n"
            "Each retry is logged with level WARNING including attempt number, status code, "
            "and cumulative elapsed time. Added unit tests mocking httpx responses.\n"
            "---\nLooks good. One nit: should we make the max_attempts configurable via env var?\n"
            "---\nDone, added RETRY_MAX_ATTEMPTS with default 5."
        ),
        updated_at=datetime(2024, 3, 18, tzinfo=timezone.utc),
        metadata={"repo": "acme/backend", "number": 204, "state": "merged",
                  "base_branch": "main", "labels": ["enhancement"]},
        doc_id="github::pull_request::acme/backend::pr::204",
    ),
    NormalizedDocument(
        source="github", source_native_id="acme/backend::issue::87",
        doc_type="issue", url="https://github.com/acme/backend/issues/87",
        title="Database migration rollback procedure",
        raw_text=(
            "Database migration rollback procedure\n\n"
            "After the incident on Feb 12 where a bad migration locked the users table for "
            "3 minutes, we need a documented rollback procedure. Current state: we use Alembic "
            "for migrations but have no automated rollback path.\n\n"
            "Proposed procedure:\n1. Always write a downgrade() function in every migration\n"
            "2. Test rollback in staging before applying to prod\n"
            "3. Use blue-green deployment for schema changes that alter columns\n"
            "4. Keep a runbook in Notion with step-by-step rollback commands\n\n"
            "---\nAlso: we should add a pre-deploy check that verifies the migration is "
            "backward-compatible (no column drops, no NOT NULL without defaults).\n"
            "---\nCreated the Notion runbook. Link: notion.so/acme/db-migration-runbook"
        ),
        updated_at=datetime(2024, 2, 20, tzinfo=timezone.utc),
        metadata={"repo": "acme/backend", "number": 87, "state": "closed",
                  "labels": ["ops", "database"]},
        doc_id="github::issue::acme/backend::issue::87",
    ),
    NormalizedDocument(
        source="notion", source_native_id="notion-page-auth-001",
        doc_type="notion_page", url="https://notion.so/acme/auth-token-spec",
        title="Authentication Token Lifecycle Spec",
        raw_text=(
            "Authentication Token Lifecycle Spec\n\n"
            "Overview\nOur auth system uses short-lived access tokens (15 min) with long-lived "
            "refresh tokens (30 days). Access tokens are JWTs signed with RS256. Refresh tokens "
            "are opaque strings stored in the sessions table.\n\n"
            "Token Refresh Flow\n1. Client sends expired access token + refresh token to POST /auth/refresh\n"
            "2. Server validates refresh token against sessions table\n"
            "3. If valid and not expired: issue new access token, rotate refresh token\n"
            "4. If expired: return 401, client must re-authenticate\n\n"
            "Token Revocation\nOn logout, the refresh token is deleted from sessions table. "
            "Access tokens remain valid until expiry (max 15 min exposure window). For "
            "immediate revocation (security incidents), we maintain a token blacklist in Redis "
            "with TTL matching the access token lifetime.\n\n"
            "Security Considerations\n- Refresh tokens are single-use (rotation on each refresh)\n"
            "- Token theft detection: if a rotated refresh token is reused, revoke the entire session\n"
            "- Access tokens include user_id, org_id, and role claims\n"
            "- Never store tokens in localStorage; use httpOnly secure cookies"
        ),
        updated_at=datetime(2024, 4, 1, tzinfo=timezone.utc),
        metadata={"parent_id": "acme-workspace", "database_id": None},
        doc_id="notion::notion_page::notion-page-auth-001",
    ),
    NormalizedDocument(
        source="notion", source_native_id="notion-page-api-rate-limit",
        doc_type="notion_page", url="https://notion.so/acme/api-rate-limiting",
        title="API Rate Limiting Strategy",
        raw_text=(
            "API Rate Limiting Strategy\n\n"
            "Current Implementation\nWe use a token bucket algorithm implemented in Redis. "
            "Each API key gets a bucket with capacity 1000 tokens and refill rate of 100 tokens/sec.\n\n"
            "Rate Limit Headers\nEvery response includes:\n"
            "- X-RateLimit-Limit: 1000\n- X-RateLimit-Remaining: <tokens left>\n"
            "- X-RateLimit-Reset: <unix timestamp when bucket refills>\n\n"
            "When rate limited, we return 429 Too Many Requests with a Retry-After header.\n\n"
            "Tiered Limits\n- Free tier: 100 req/min\n- Pro tier: 1000 req/min\n"
            "- Enterprise: custom, negotiated per contract\n\n"
            "Monitoring\nRate limit hits are tracked in Datadog with tags for api_key, endpoint, "
            "and tier. Alert threshold: >5% of requests rate-limited over 5 min window.\n\n"
            "Known Issues\n- The current implementation doesn't handle burst traffic well for "
            "websocket connections\n- Need to add per-endpoint rate limits (not just global per key)"
        ),
        updated_at=datetime(2024, 3, 25, tzinfo=timezone.utc),
        metadata={"parent_id": "acme-workspace", "database_id": None},
        doc_id="notion::notion_page::notion-page-api-rate-limit",
    ),
    NormalizedDocument(
        source="github", source_native_id="acme/backend::md::docs/async-errors.md",
        doc_type="markdown_file", url="https://github.com/acme/backend/blob/main/docs/async-errors.md",
        title="docs/async-errors.md",
        raw_text=(
            "# Error Handling in Async Code\n\n"
            "## General Principles\n"
            "All async functions must catch and handle exceptions explicitly. Unhandled exceptions "
            "in async tasks are silently swallowed by the event loop and lead to data loss.\n\n"
            "## Pattern: Structured Error Handling\n```python\nasync def process_item(item):\n"
            "    try:\n        result = await external_api.call(item)\n"
            "        return result\n    except httpx.TimeoutException:\n"
            "        logger.warning(f'Timeout processing {item.id}')\n"
            "        raise  # Let retry logic handle it\n"
            "    except ValidationError as e:\n"
            "        logger.error(f'Validation failed for {item.id}: {e}')\n"
            "        return None  # Skip bad items\n```\n\n"
            "## Common Pitfalls\n"
            "1. **Bare except clauses** - Never use bare `except:` in async code. It catches "
            "CancelledError and breaks task cancellation.\n"
            "2. **Fire and forget tasks** - Always store task references and await them. "
            "Use asyncio.TaskGroup (Python 3.11+) for structured concurrency.\n"
            "3. **Blocking the event loop** - CPU-bound work or synchronous I/O in async "
            "functions blocks all other tasks. Use run_in_executor for these.\n\n"
            "## Circuit Breaker Pattern\n"
            "For external service calls, we use a circuit breaker that opens after 5 consecutive "
            "failures and closes after 30 seconds. This prevents cascade failures when a "
            "downstream service is unhealthy."
        ),
        updated_at=datetime(2024, 4, 5, tzinfo=timezone.utc),
        metadata={"repo": "acme/backend", "path": "docs/async-errors.md"},
        doc_id="github::markdown_file::acme/backend::md::docs/async-errors.md",
    ),
    NormalizedDocument(
        source="notion", source_native_id="notion-page-onboarding",
        doc_type="notion_page", url="https://notion.so/acme/onboarding",
        title="New Engineer Onboarding Checklist",
        raw_text=(
            "New Engineer Onboarding Checklist\n\n"
            "Week 1\n- Set up development environment (see Dev Setup Guide)\n"
            "- Get access to GitHub org, Notion workspace, Slack, Datadog, AWS console\n"
            "- Clone the monorepo and run the test suite locally\n"
            "- Read the Architecture Decision Records in docs/adr/\n"
            "- Pair with your onboarding buddy on a small bug fix\n\n"
            "Week 2\n- Complete the authentication flow walkthrough\n"
            "- Review the API rate limiting spec and database schema docs\n"
            "- Ship your first PR (aim for something small but real)\n"
            "- Set up your local Datadog dashboard\n\n"
            "Week 3-4\n- Pick up a medium-sized feature ticket\n"
            "- Do your first code review for someone else\n"
            "- Join the on-call shadow rotation\n"
            "- Schedule 1:1s with leads from other teams\n\n"
            "Key Resources\n- Monorepo: github.com/acme/backend\n"
            "- Notion workspace: notion.so/acme\n"
            "- Slack: #engineering, #incidents, #deploys\n"
            "- Datadog: app.datadoghq.com/acme"
        ),
        updated_at=datetime(2024, 3, 10, tzinfo=timezone.utc),
        metadata={"parent_id": "acme-workspace", "database_id": None},
        doc_id="notion::notion_page::notion-page-onboarding",
    ),
    NormalizedDocument(
        source="github", source_native_id="acme/backend::issue::142",
        doc_type="issue", url="https://github.com/acme/backend/issues/142",
        title="Connection pool exhaustion under load",
        raw_text=(
            "Connection pool exhaustion under load\n\n"
            "During the load test on March 5th, we observed connection pool exhaustion after "
            "~2000 concurrent users. The pool is configured at max=20 connections. Symptoms: "
            "requests queue up waiting for connections, p99 latency spikes to 12s, eventually "
            "timeout errors cascade.\n\n"
            "Root cause: several async endpoints hold connections across multiple await points "
            "(fetch from DB, call external API, write back to DB) instead of acquiring/releasing "
            "per query.\n\n"
            "Fix:\n1. Refactor endpoints to use short-lived connection leases\n"
            "2. Increase pool max to 50 with overflow to 100\n"
            "3. Add connection checkout timeout of 5s (fail fast instead of queue indefinitely)\n"
            "4. Add pool utilization metrics to Datadog (active/idle/overflow)\n\n"
            "---\nAlso found that the health check endpoint was holding a connection open for the "
            "entire request lifecycle. Fixed in hotfix PR #198."
        ),
        updated_at=datetime(2024, 3, 8, tzinfo=timezone.utc),
        metadata={"repo": "acme/backend", "number": 142, "state": "closed",
                  "labels": ["bug", "performance"]},
        doc_id="github::issue::acme/backend::issue::142",
    ),
]


def main():
    print("Upserting documents...")
    for doc in DOCS:
        upsert_document(doc)
        print(f"  {doc.doc_id}")

    print("\nChunking and embedding...")
    total_chunks = 0
    for doc in DOCS:
        chunks = chunk_document(doc)
        if not chunks:
            continue
        embed_chunks(chunks)
        upsert_chunks(chunks)
        mark_document_embedded(doc.doc_id)
        total_chunks += len(chunks)
        print(f"  {doc.doc_id}: {len(chunks)} chunks")

    print(f"\nDone. {len(DOCS)} docs, {total_chunks} chunks embedded.")


if __name__ == "__main__":
    main()
