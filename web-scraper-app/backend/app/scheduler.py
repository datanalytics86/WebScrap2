"""Configuración del scheduler con APScheduler."""
from __future__ import annotations

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .database import SessionLocal
from .services.scraper_service import run_scrapers

LOGGER = logging.getLogger(__name__)


def _scheduled_job() -> None:
    """Job programado para ejecutar scrapers."""
    session = SessionLocal()
    try:
        LOGGER.info("Ejecutando scraping programado")
        run_scrapers(session)
    finally:
        session.close()


def start_scheduler() -> BackgroundScheduler:
    """Inicia el scheduler con intervalo de 6 horas."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(_scheduled_job, IntervalTrigger(hours=6), id="scraper_job", replace_existing=True)
    scheduler.start()
    LOGGER.info("Scheduler iniciado")
    return scheduler
