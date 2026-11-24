#!/bin/sh
# entrypoint.sh — arranque del contenedor `api`: aplica las migraciones y lanza el servidor.
# La espera a Postgres la garantiza `depends_on: service_healthy` en docker-compose.
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000