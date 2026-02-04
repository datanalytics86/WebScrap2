"""App Streamlit para scraping rápido y exportación a Excel."""
from __future__ import annotations

import io
from typing import List, Dict, Any

from openpyxl import Workbook
import streamlit as st
from bs4 import BeautifulSoup
import requests


st.set_page_config(page_title="Web Scraper Streamlit", layout="wide")

st.title("Web Scraper con Exportación a Excel")
st.markdown(
    "Ingresa una URL y ejecuta el scraping **a demanda**. "
    "Si el sitio no es conocido, agrega selectores CSS para nombre y precio."
)
st.caption(
    "Para sitios genéricos debes completar selectores CSS de nombre y precio "
    "(puedes dejar enlace vacío si no aplica)."
)

url = st.text_input("URL del sitio", "https://listado.mercadolibre.cl/notebook")
name_selector = st.text_input("Selector CSS para nombre", "h2.ui-search-item__title")
price_selector = st.text_input("Selector CSS para precio", "span.andes-money-amount__fraction")
link_selector = st.text_input("Selector CSS para enlace (opcional)", "a.ui-search-item__group__element")
limit = st.number_input("Máximo de productos", min_value=1, max_value=200, value=50)


def generic_scrape(
    target_url: str, name_css: str, price_css: str, link_css: str, max_items: int
) -> List[Dict[str, Any]]:
    """Scraping genérico basado en selectores CSS."""
    if not name_css or not price_css:
        raise ValueError("Debes definir selectores CSS para nombre y precio en sitios genéricos.")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(target_url, headers=headers, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    names = [node.get_text(strip=True) for node in soup.select(name_css)]
    prices_raw = [node.get_text(strip=True) for node in soup.select(price_css)]
    links = [node.get("href") for node in soup.select(link_css)] if link_css else []

    results: List[Dict[str, Any]] = []
    for idx, (name, price) in enumerate(zip(names, prices_raw)):
        if idx >= max_items:
            break
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
        link_value = links[idx] if idx < len(links) else None
        results.append({"name": name, "price": price_value, "url": link_value})

    return results


if st.button("Ejecutar scraping a demanda"):
    with st.spinner("Scrapeando datos..."):
        try:
            data = generic_scrape(url, name_selector, price_selector, link_selector, limit)

            if not data:
                st.warning("No se encontraron productos.")
            else:
                st.success(f"Productos encontrados: {len(data)}")
                st.dataframe(data, use_container_width=True)

                output = io.BytesIO()
                workbook = Workbook()
                sheet = workbook.active
                headers = list(data[0].keys())
                sheet.append(headers)
                for row in data:
                    sheet.append([row.get(header) for header in headers])
                workbook.save(output)
                st.download_button(
                    label="Descargar Excel (.xlsx)",
                    data=output.getvalue(),
                    file_name="productos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        except Exception as exc:  # pylint: disable=broad-except
            st.error(f"Error al ejecutar scraping: {exc}")
