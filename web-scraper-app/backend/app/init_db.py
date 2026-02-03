"""Script de inicialización manual de la base de datos."""
from __future__ import annotations

from .database import init_db, SessionLocal
from .models import Website


def main() -> None:
    """Crea tablas y sitios por defecto."""
    init_db()
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


if __name__ == "__main__":
    main()
