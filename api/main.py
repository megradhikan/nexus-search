import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import search as search_router
from api.routes import health as health_router
from nexus.retrieval.rrf import load_chunk_cache
from nexus.retrieval.bm25_index import load_index, build_index, is_stale

logger = logging.getLogger(__name__)

app = FastAPI(title="NexusSearch API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_scheduler = None


@app.on_event("startup")
def startup():
    global _scheduler
    load_chunk_cache()
    if is_stale() or not load_index():
        logger.info("Building BM25 index...")
        build_index()
    else:
        logger.info("BM25 index loaded from disk.")
    if os.getenv("NEXUS_DISABLE_SCHEDULER") != "1":
        from scheduler.runner import start_scheduler
        _scheduler = start_scheduler()


@app.on_event("shutdown")
def shutdown():
    if _scheduler:
        _scheduler.shutdown(wait=False)


app.include_router(search_router.router)
app.include_router(health_router.router)
