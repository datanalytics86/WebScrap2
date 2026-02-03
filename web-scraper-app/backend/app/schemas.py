"""Esquemas Pydantic para la API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class WebsiteBase(BaseModel):
    name: str
    base_url: str
    active: bool = True


class WebsiteCreate(WebsiteBase):
    pass


class WebsiteOut(WebsiteBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    website_id: int
    name: str
    url: str
    current_price: float
    original_price: Optional[float]
    discount: Optional[float]
    last_scraped: datetime


class ProductOut(ProductBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class PriceHistoryOut(BaseModel):
    id: int
    product_id: int
    price: float
    scraped_at: datetime

    class Config:
        orm_mode = True


class ScrapingLogOut(BaseModel):
    id: int
    website_id: int
    status: str
    products_found: int
    errors: Optional[str]
    duration: float
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        orm_mode = True


class StatsOut(BaseModel):
    total_products: int
    last_run: Optional[datetime]
    discount_over_20: int
    active_websites: int


class ScrapeManualRequest(BaseModel):
    website_ids: Optional[List[int]] = None
