"""App Streamlit para scraping rápido y exportación a Excel."""
from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import requests

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_PATH = (CURRENT_DIR / "backend").resolve()
if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))

from app.scrapers.mercadolibre_scraper import MercadoLibreScraper
from app.scrapers.falabella_scraper import FalabellaScraper


st.set_page_config(page_title="Web Scraper Streamlit", layout="wide")

st.title("Web Scraper con Exportación a Excel")
st.markdown(
    "Ingresa una URL y ejecuta el scraping **a demanda**. "
    "Si el sitio no es conocido, agrega selectores CSS para nombre y precio."
)

url = st.text_input("URL del sitio", "https://listado.mercadolibre.cl/notebook")
name_selector = st.text_input("Selector CSS para nombre (opcional)", "")
price_selector = st.text_input("Selector CSS para precio (opcional)", "")


def generic_scrape(target_url: str, name_css: str, price_css: str) -> List[Dict[str, Any]]:
    """Scraping genérico basado en selectores CSS."""
    if not name_css or not price_css:
        raise ValueError("Debes definir selectores CSS para nombre y precio en sitios genéricos.")

    response = requests.get(target_url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    names = [node.get_text(strip=True) for node in soup.select(name_css)]
    prices_raw = [node.get_text(strip=True) for node in soup.select(price_css)]

    results: List[Dict[str, Any]] = []
    for name, price in zip(names, prices_raw):
        cleaned = (
            price.replace("$", "")
            .replace(".", "")
            .replace("CLP", "")
            .replace(" ", "")
        )
        try:
            price_value = float(cleaned)
        except ValueError:
            price_value = None
        results.append({"name": name, "price": price_value})

    return results


if st.button("Ejecutar scraping a demanda"):
    with st.spinner("Scrapeando datos..."):
        try:
            data: List[Dict[str, Any]]
            if "mercadolibre" in url:
                data = MercadoLibreScraper(url).scrape()
            elif "falabella" in url:
                data = FalabellaScraper(url).scrape()
            else:
                data = generic_scrape(url, name_selector, price_selector)

            if not data:
                st.warning("No se encontraron productos.")
            else:
                df = pd.DataFrame(data)
                st.success(f"Productos encontrados: {len(df)}")
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                df.to_excel(output, index=False)
                st.download_button(
                    label="Descargar Excel (.xlsx)",
                    data=output.getvalue(),
                    file_name="productos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        except Exception as exc:  # pylint: disable=broad-except
            st.error(f"Error al ejecutar scraping: {exc}")
