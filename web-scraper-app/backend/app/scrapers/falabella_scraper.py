"""Scraper para Falabella Chile."""
from __future__ import annotations

import logging
from typing import List, Dict, Any

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

LOGGER = logging.getLogger(__name__)


class FalabellaScraper(BaseScraper):
    """Scraper especializado para Falabella Chile."""

    CATEGORY_URL = "https://www.falabella.com/falabella-cl/category/cat70002/Tecnologia"

    def scrape(self) -> List[Dict[str, Any]]:
        """Extrae productos de la categoría tecnología."""
        LOGGER.info("Iniciando scraping Falabella")
        response = self._request_with_retries(self.CATEGORY_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        items: List[Dict[str, Any]] = []

        for card in soup.select("div.pod-item"):
            name_tag = card.select_one("b.pod-subTitle")
            price_tag = card.select_one("li.price-0 span")
            original_tag = card.select_one("li.price-1 span")
            link_tag = card.select_one("a.pod-link")

            if not name_tag or not price_tag or not link_tag:
                continue

            name = name_tag.get_text(strip=True)
            price_text = price_tag.get_text(strip=True).replace("$", "").replace(".", "")
            try:
                price = float(price_text)
            except ValueError:
                continue

            original_price = None
            discount = None
            if original_tag:
                original_text = original_tag.get_text(strip=True).replace("$", "").replace(".", "")
                try:
                    original_price = float(original_text)
                except ValueError:
                    original_price = None

            if original_price and original_price > 0:
                discount = round((1 - price / original_price) * 100, 2)

            items.append(
                {
                    "name": name,
                    "url": link_tag.get("href"),
                    "current_price": price,
                    "original_price": original_price,
                    "discount": discount,
                }
            )

        LOGGER.info("Falabella: %s productos extraídos", len(items))
        return items
