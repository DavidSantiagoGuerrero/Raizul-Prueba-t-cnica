#!/bin/sh
# entrypoint.sh — arranque del contenedor `api`: aplica las migraciones y lanza el servidor.
# La espera a Postgres la garantiza `depends_on: service_healthy` en docker-compose.
set -e

echo "========================================"
echo "Ejecutando migraciones..."
echo "========================================"
alembic upgrade head

echo "========================================"
echo "Ejecutando pruebas..."
echo "========================================"
pytest -v

echo "========================================"
echo "Todas las pruebas pasaron correctamente."
echo "Iniciando servidor FastAPI..."
echo "========================================"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000