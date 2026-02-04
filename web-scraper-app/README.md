# Web Scraper App con Dashboard

Proyecto completo de web scraping con backend FastAPI, scheduler y dashboard web. Incluye una app Streamlit para ejecutar scraping por URL y exportar a Excel.

## Requisitos del sistema

- Python 3.10+
- SQLite (incluido en Python)
- Navegador moderno para el dashboard

## Instalación paso a paso

```bash
cd web-scraper-app
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

python -m backend.app.init_db

uvicorn backend.app.main:app --reload --port 8000

cd frontend
python -m http.server 8080

streamlit run streamlit_app.py
Ingresa una URL válida y los selectores CSS para nombre y precio.

El scraping se ejecuta solo cuando presionas el botón (no hay scraping automático).

Descarga el Excel desde el botón de exportación (.xlsx).

Deploy en Streamlit Community Cloud
Al crear la app en Streamlit Cloud usa:

Repository: https://github.com/<tu-usuario>/<tu-repo>

Branch: main

Main file path: web-scraper-app/streamlit_app.py

Nota: Streamlit Cloud instala dependencias desde requirements.txt en la raíz del repo.
Para acelerar el deploy, ese archivo contiene solo las librerías mínimas de Streamlit.

Endpoints principales
GET /api/websites

POST /api/websites

GET /api/products

GET /api/products/{id}/history

POST /api/scrape/manual

GET /api/scraping-logs

GET /api/stats

Cómo agregar nuevos scrapers
Crea un archivo en backend/app/scrapers/ extendiendo BaseScraper.

Implementa el método scrape() retornando una lista de productos.

Registra el scraper en services/scraper_service.py dentro de _select_scraper.

Agrega el sitio en la tabla websites (API o script de inicialización).

Notas de configuración
La base de datos SQLite se guarda en scraper.db.

El scheduler ejecuta scraping cada 6 horas.

Puedes ajustar DATABASE_URL en backend/.env.example.

Consideraciones
Los sitios pueden cambiar estructura HTML con el tiempo.

El scraper incluye rotación de User-Agent, delays aleatorios y reintentos.