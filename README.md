# NexusSearch

> Mini enterprise knowledge search engine with hybrid BM25 + dense retrieval over GitHub and Notion. Built to demonstrate production search architecture.

## What it does

NexusSearch ingests documents from GitHub (issues, pull requests, markdown files) and Notion pages, normalizes them into a unified schema, splits them into overlapping chunks, and embeds each chunk using a local sentence-transformer model. Embeddings are stored in PostgreSQL via the pgvector extension alongside the raw chunk text and metadata.

At query time, NexusSearch runs both a BM25 lexical search over an in-process index and a cosine-similarity vector search against pgvector. The two result lists are fused with Reciprocal Rank Fusion (k=60) and returned as a ranked list of chunks with source attribution, relevance scores, and direct links. An incremental scheduler keeps the index fresh by polling connectors on a configurable interval.

## Architecture

```
GitHub / Notion
      │
      ▼
  Connectors  ──►  NormalizedDocument
      │
      ▼
   Chunker (RecursiveCharacterTextSplitter, 512 tok / 64 overlap)
      │
      ▼
  Embedder (all-MiniLM-L6-v2, 384-dim, L2-normalized)
      │
      ├──► pgvector (chunks table, cosine search)
      │
      └──► BM25Okapi in-memory (rank_bm25)
                │
                ▼
          RRF Fusion (k=60)
                │
                ▼
        FastAPI  /search
```

## Tech stack

| Component          | Library                        | Why                                                          |
|--------------------|--------------------------------|--------------------------------------------------------------|
| Vector store       | pgvector                       | Co-located with metadata in Postgres, no extra infra         |
| Lexical retrieval  | rank_bm25                      | In-process, no server needed, fast enough at this scale      |
| Reranking          | RRF k=60                       | Parameter-free fusion, robust across score distributions     |
| Embeddings         | all-MiniLM-L6-v2               | Local inference, 384-dim, strong quality/speed tradeoff      |
| Scheduler          | APScheduler                    | In-process job chain, Postgres-backed job store              |
| Web framework      | FastAPI                        | Async + Pydantic validation, minimal boilerplate             |

## Eval results

Run `python -m nexus.eval` to populate.

| Retriever    | MRR       | NDCG@5     |
|--------------|-----------|------------|
| Hybrid (RRF) | ---       | ---        |
| BM25 only    | ---       | ---        |
| Dense only   | ---       | ---        |

## Quickstart

**Prerequisites:** Python 3.11+, Docker

```bash
git clone <repo>
cd nexus-search
cp .env.example .env          # fill in GITHUB_TOKEN, NOTION_TOKEN
docker-compose up -d
pip install -e .
python -m nexus.db.migrate
python seed_demo.py               # or: python -m nexus.ingest (with real tokens)
uvicorn api.main:app --reload
```

### UI

```bash
cd ui && npm install && npm run dev
```

The UI proxies API calls to `localhost:8000`. Run the FastAPI server first.

## API reference

### POST /search

```json
{ "query": "retry with exponential backoff", "top_k": 10, "sources": ["github"] }
```

```json
{
  "query": "...",
  "results": [{ "rank": 1, "doc_id": "...", "title": "...", "source": "github",
                "url": "...", "excerpt": "...", "rrf_score": 0.032,
                "retrieval_sources": ["bm25", "dense"] }],
  "latency_ms": 42.1,
  "total_chunks_indexed": 1500
}
```

### POST /feedback

```json
{ "query_text": "...", "doc_id": "...", "rank_at_feedback": 1, "signal": "positive" }
```

### GET /health

```json
{ "status": "ok", "chunks_indexed": 1500, "bm25_index_loaded": true, "freshness_lag_minutes": 12.4 }
```

## Design decisions and tradeoffs

### Chunking strategy

Chunks are 512 tokens with a 64-token overlap using `RecursiveCharacterTextSplitter`. 512 tokens balances context density against embedding quality — larger chunks dilute the embedding signal; smaller chunks lose surrounding context. The overlap ensures that sentences split across chunk boundaries still appear in at least one complete chunk, improving recall for phrase-level queries.

### pgvector vs dedicated vector DB

At the scale NexusSearch targets (tens of thousands of chunks), keeping vectors in Postgres eliminates an entire infrastructure dependency while retaining transactional consistency between document metadata and embeddings. A dedicated vector DB becomes worthwhile when you need horizontal read scaling or approximate-index tuning beyond what IVFFlat provides — typically above a few million vectors.

### RRF vs linear score combination

RRF only requires ranks, not calibrated scores. BM25 and cosine similarity live on incompatible scales, so any linear combination needs a tuned weight — which overfits to your eval set and breaks when the corpus shifts. RRF is parameter-free once k is chosen, and k=60 is robust across a wide range of corpus sizes. It consistently outperforms untuned linear fusion in practice.

### In-process BM25 vs Elasticsearch

Elasticsearch introduces network latency, operational overhead, and a JVM to manage. For corpora under ~5M documents, `rank_bm25` running in-process with the API server is faster end-to-end and far simpler to operate. The migration path is straightforward: swap `search_bm25()` for an ES query and keep the RRF layer unchanged.

### Incremental polling vs webhooks

The current approach polls connectors on a fixed interval. This is operationally simple — no public endpoint required, no webhook registration per repo. The tradeoff is latency: new content appears after at most `POLLING_INTERVAL_MINUTES`. Migrating to webhooks requires exposing an HTTPS endpoint, handling webhook verification per source, and managing delivery retries, but reduces indexing lag to seconds for high-frequency sources like active GitHub repos.

## Open questions

- **Re-ranking model**: Should a cross-encoder re-ranker (e.g., ms-marco-MiniLM) be added as a third stage after RRF? It improves precision at the cost of ~20-50ms per query and requires a GPU or batched inference to stay within latency budget.
- **Multi-tenancy**: The current schema has no user or team isolation. Adding row-level security in Postgres or a `tenant_id` column would be required before exposing this to multiple teams with separate data boundaries.
- **Embedding model upgrades**: Switching from all-MiniLM-L6-v2 to a larger model (e.g., all-mpnet-base-v2 or a domain-fine-tuned model) requires re-embedding all chunks. A migration flag and a background re-embedding job would minimize downtime.
- **BM25 index staleness**: The current staleness check compares file mtime against `MAX(embedded_at)`. Under heavy concurrent writes this can cause spurious rebuilds. A version counter in the database would be more reliable.
- **Notion API rate limits**: The current connector sleeps 350ms between block-children calls. For large Notion workspaces this makes full ingestion slow. Batching or using Notion's official rate-limit headers would improve throughput.
