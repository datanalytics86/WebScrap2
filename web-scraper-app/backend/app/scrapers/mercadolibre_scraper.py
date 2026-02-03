"""Scraper para MercadoLibre Chile."""
from __future__ import annotations

import logging
from typing import List, Dict, Any

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

LOGGER = logging.getLogger(__name__)


class MercadoLibreScraper(BaseScraper):
    """Scraper especializado para MercadoLibre Chile."""

    SEARCH_URL = "https://listado.mercadolibre.cl/notebook"

    def scrape(self) -> List[Dict[str, Any]]:
        """Extrae productos de la búsqueda de notebooks."""
        LOGGER.info("Iniciando scraping MercadoLibre")
        response = self._request_with_retries(self.SEARCH_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        items = []

        for card in soup.select("li.ui-search-layout__item"):
            name_tag = card.select_one("h2.ui-search-item__title")
            price_tag = card.select_one("span.andes-money-amount__fraction")
            original_tag = card.select_one("span.andes-money-amount--previous .andes-money-amount__fraction")
            link_tag = card.select_one("a.ui-search-item__group__element")

            if not name_tag or not price_tag or not link_tag:
                continue

            name = name_tag.get_text(strip=True)
            price = float(price_tag.get_text(strip=True).replace(".", ""))
            original_price = None
            discount = None

            if original_tag:
                original_price = float(original_tag.get_text(strip=True).replace(".", ""))
                if original_price > 0:
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

        LOGGER.info("MercadoLibre: %s productos extraídos", len(items))
        return items
