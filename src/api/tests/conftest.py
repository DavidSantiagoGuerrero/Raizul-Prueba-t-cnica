"""Configuración compartida de pytest: base de datos de pruebas y cliente HTTP.

Las pruebas usan una base **separada** (`<nombre>_test`, derivada de DATABASE_URL
o de TEST_DATABASE_URL), así que nunca tocan los datos de desarrollo. Se crea sola
si no existe y su esquema se construye con las migraciones reales de Alembic.
Antes de cada prueba se vacían las tablas.

Importante: DATABASE_URL se redefine ANTES de importar `app`, porque
`app.db.session` lee esa variable al importarse.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

def test_database_url() -> URL:
    """URL de la base de pruebas: TEST_DATABASE_URL o DATABASE_URL + sufijo `_test`."""
    url = make_url(os.environ.get("TEST_DATABASE_URL") or os.environ["DATABASE_URL"])
    if not (url.database or "").endswith("_test"):
        url = url.set(database=f"{url.database}_test")
    return url

TEST_URL = test_database_url()
os.environ["DATABASE_URL"] = TEST_URL.render_as_string(hide_password=False)

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.db.connection import engine
from app.main import app

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"

def create_database_if_missing() -> None:
    """Crea la base de pruebas conectándose a la base de mantenimiento `postgres`."""
    admin = create_engine(TEST_URL.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_URL.database}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_URL.database}"'))
    admin.dispose()

@pytest.fixture(scope="session", autouse=True)
def database():
    """Deja la base de pruebas vacía y le aplica las migraciones (una vez por sesión)."""
    create_database_if_missing()
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    yield
    engine.dispose()

@pytest.fixture(autouse=True)
def clean_tables(database):
    """Vacía las tablas antes de cada prueba y reinicia los ids."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE producers, farms RESTART IDENTITY CASCADE"))

@pytest.fixture
def client() -> TestClient:
    """Cliente HTTP contra la app FastAPI."""
    return TestClient(app)

@pytest.fixture
def producer_payload() -> dict:
    """Cuerpo válido para crear un productor."""
    return {"document_number": "1234567890", "full_name": "Ana Pérez", "municipality": "Tumaco"}

@pytest.fixture
def producer(client, producer_payload) -> dict:
    """Un productor ya creado (respuesta de la API)."""
    response = client.post("/producers", json=producer_payload)
    assert response.status_code == 201
    return response.json()