"""Clase base para scrapers."""
from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any

import requests

LOGGER = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


class BaseScraper(ABC):
    """Base de scrapers con utilidades compartidas."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers con User-Agent rotativo."""
        return {"User-Agent": random.choice(USER_AGENTS)}

    def _sleep_random(self) -> None:
        """Espera aleatoria entre requests."""
        delay = random.uniform(2, 5)
        LOGGER.debug("Esperando %.2f segundos antes del siguiente request", delay)
        time.sleep(delay)

    def _request_with_retries(self, url: str, retries: int = 3) -> requests.Response:
        """Realiza requests con reintentos y backoff exponencial."""
        for attempt in range(1, retries + 1):
            try:
                response = self.session.get(url, headers=self._get_headers(), timeout=20)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                wait = 2 ** attempt
                LOGGER.warning("Intento %s fallido para %s: %s", attempt, url, exc)
                if attempt == retries:
                    raise
                time.sleep(wait)
        raise RuntimeError("No se pudo completar la petición")

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """Ejecuta el scraping y retorna productos."""
        raise NotImplementedError
