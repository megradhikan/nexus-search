import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from nexus.config import get_settings
from scheduler.jobs import job_connector_sync, job_embedding_pipeline, job_bm25_rebuild

logger = logging.getLogger(__name__)


def start_scheduler(app=None) -> BackgroundScheduler:
    settings = get_settings()
    jobstores = {"default": SQLAlchemyJobStore(url=settings.database_url)}
    executors = {"default": ThreadPoolExecutor(max_workers=2)}

    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        timezone="UTC",
    )

    now = datetime.now(timezone.utc)
    interval = settings.polling_interval_minutes

    scheduler.add_job(
        job_connector_sync,
        trigger="interval",
        minutes=interval,
        id="connector_sync",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        job_embedding_pipeline,
        trigger="interval",
        minutes=interval,
        id="embedding_pipeline",
        replace_existing=True,
        misfire_grace_time=300,
        start_date=now + timedelta(minutes=2),
    )
    scheduler.add_job(
        job_bm25_rebuild,
        trigger="interval",
        minutes=interval,
        id="bm25_rebuild",
        replace_existing=True,
        misfire_grace_time=300,
        start_date=now + timedelta(minutes=4),
    )

    scheduler.start()
    logger.info(f"Scheduler started. Polling every {interval} minutes.")
    return scheduler
