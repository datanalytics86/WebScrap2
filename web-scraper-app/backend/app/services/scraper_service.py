"""Servicio para coordinar scrapers y persistencia."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import Website, Product, PriceHistory, ScrapingLog
from ..scrapers.falabella_scraper import FalabellaScraper
from ..scrapers.mercadolibre_scraper import MercadoLibreScraper

LOGGER = logging.getLogger(__name__)

SCRAPER_MAP = {
    "mercadolibre": MercadoLibreScraper,
    "falabella": FalabellaScraper,
}


def _select_scraper(website: Website):
    """Selecciona el scraper adecuado según el sitio."""
    base = website.base_url.lower()
    if "mercadolibre" in base:
        return MercadoLibreScraper(website.base_url)
    if "falabella" in base:
        return FalabellaScraper(website.base_url)
    raise ValueError(f"No hay scraper configurado para {website.base_url}")


def run_scraper(session: Session, website: Website) -> ScrapingLog:
    """Ejecuta el scraper de un sitio y guarda datos."""
    start_time = datetime.utcnow()
    log_entry = ScrapingLog(
        website_id=website.id,
        status="running",
        started_at=start_time,
        products_found=0,
    )
    session.add(log_entry)
    session.commit()

    alerts: List[str] = []

    try:
        scraper = _select_scraper(website)
        products = scraper.scrape()
        log_entry.products_found = len(products)

        for product_data in products:
            existing = session.query(Product).filter_by(url=product_data["url"]).first()
            if existing:
                previous_price = existing.current_price
                existing.current_price = product_data["current_price"]
                existing.original_price = product_data.get("original_price")
                existing.discount = product_data.get("discount")
                existing.last_scraped = datetime.utcnow()
                session.add(existing)

                if previous_price > 0:
                    change = abs(existing.current_price - previous_price) / previous_price * 100
                    if change > 10:
                        alerts.append(
                            f"Cambio >10% en {existing.name}: {previous_price} -> {existing.current_price}"
                        )
            else:
                existing = Product(
                    website_id=website.id,
                    name=product_data["name"],
                    url=product_data["url"],
                    current_price=product_data["current_price"],
                    original_price=product_data.get("original_price"),
                    discount=product_data.get("discount"),
                    last_scraped=datetime.utcnow(),
                )
                session.add(existing)

            session.flush()
            history = PriceHistory(
                product_id=existing.id,
                price=existing.current_price,
                scraped_at=datetime.utcnow(),
            )
            session.add(history)

        log_entry.status = "success"
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Error en scraping")
        log_entry.status = "failed"
        log_entry.errors = str(exc)
    finally:
        if alerts:
            alert_text = " | ".join(alerts)
            log_entry.errors = f"{log_entry.errors or ''} {alert_text}".strip()

        log_entry.finished_at = datetime.utcnow()
        log_entry.duration = (log_entry.finished_at - start_time).total_seconds()
        session.add(log_entry)
        session.commit()

    return log_entry


def run_scrapers(session: Session, website_ids: Optional[List[int]] = None) -> List[ScrapingLog]:
    """Ejecuta scrapers para los sitios activos o seleccionados."""
    query = session.query(Website).filter_by(active=True)
    if website_ids:
        query = query.filter(Website.id.in_(website_ids))

    logs = []
    for website in query.all():
        logs.append(run_scraper(session, website))
    return logs
