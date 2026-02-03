"""Aplicación FastAPI principal."""
from __future__ import annotations

import logging
import os
from typing import Generator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import SessionLocal, init_db
from .models import Website, Product, PriceHistory, ScrapingLog
from .schemas import (
    WebsiteCreate,
    WebsiteOut,
    ProductOut,
    PriceHistoryOut,
    ScrapingLogOut,
    StatsOut,
    ScrapeManualRequest,
)
from .scheduler import start_scheduler
from .services.scraper_service import run_scrapers

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
LOGGER = logging.getLogger(__name__)

app = FastAPI(title="Web Scraper Dashboard", version="1.0.0")

allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = None


def get_db() -> Generator[Session, None, None]:
    """Dependencia de sesión DB."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.on_event("startup")
def on_startup() -> None:
    """Inicializa BD y scheduler."""
    global scheduler  # noqa: PLW0603
    init_db()
    _seed_websites()
    scheduler = start_scheduler()


@app.on_event("shutdown")
def on_shutdown() -> None:
    """Apaga scheduler."""
    if scheduler:
        scheduler.shutdown()


def _seed_websites() -> None:
    """Crea sitios por defecto si no existen."""
    session = SessionLocal()
    try:
        if session.query(Website).count() == 0:
            session.add_all(
                [
                    Website(name="MercadoLibre", base_url="https://www.mercadolibre.cl", active=True),
                    Website(name="Falabella", base_url="https://www.falabella.com/falabella-cl", active=True),
                ]
            )
            session.commit()
    finally:
        session.close()


@app.get("/api/websites", response_model=List[WebsiteOut])
def list_websites(session: Session = Depends(get_db)) -> List[Website]:
    """Lista sitios disponibles."""
    return session.query(Website).all()


@app.post("/api/websites", response_model=WebsiteOut)
def create_website(payload: WebsiteCreate, session: Session = Depends(get_db)) -> Website:
    """Agrega un nuevo sitio."""
    website = Website(**payload.dict())
    session.add(website)
    session.commit()
    session.refresh(website)
    return website


@app.get("/api/products", response_model=List[ProductOut])
def list_products(
    website_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("price"),
    session: Session = Depends(get_db),
) -> List[Product]:
    """Lista productos con filtros."""
    query = session.query(Product)
    if website_id:
        query = query.filter(Product.website_id == website_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if sort_by == "discount":
        query = query.order_by(Product.discount.desc().nullslast())
    elif sort_by == "date":
        query = query.order_by(Product.last_scraped.desc())
    else:
        query = query.order_by(Product.current_price.asc())

    return query.all()


@app.get("/api/products/{product_id}/history", response_model=List[PriceHistoryOut])
def product_history(product_id: int, session: Session = Depends(get_db)) -> List[PriceHistory]:
    """Histórico de precios de un producto."""
    history = (
        session.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.scraped_at.asc())
        .all()
    )
    if not history:
        raise HTTPException(status_code=404, detail="Histórico no encontrado")
    return history


@app.post("/api/scrape/manual", response_model=List[ScrapingLogOut])
def manual_scrape(payload: ScrapeManualRequest, session: Session = Depends(get_db)) -> List[ScrapingLog]:
    """Ejecuta scraping manual."""
    return run_scrapers(session, payload.website_ids)


@app.get("/api/scraping-logs", response_model=List[ScrapingLogOut])
def scraping_logs(session: Session = Depends(get_db)) -> List[ScrapingLog]:
    """Retorna los últimos 50 logs."""
    return (
        session.query(ScrapingLog)
        .order_by(ScrapingLog.started_at.desc())
        .limit(50)
        .all()
    )


@app.get("/api/stats", response_model=StatsOut)
def stats(session: Session = Depends(get_db)) -> StatsOut:
    """Estadísticas generales."""
    total_products = session.query(Product).count()
    last_run = session.query(ScrapingLog).order_by(ScrapingLog.started_at.desc()).first()
    discount_over_20 = session.query(Product).filter(Product.discount >= 20).count()
    active_websites = session.query(Website).filter(Website.active.is_(True)).count()

    return StatsOut(
        total_products=total_products,
        last_run=last_run.started_at if last_run else None,
        discount_over_20=discount_over_20,
        active_websites=active_websites,
    )
