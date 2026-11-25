# Dockerfile de la API: imagen de Python con las dependencias instaladas.
# Al iniciar ejecuta entrypoint.sh (migraciones de Alembic + uvicorn).
FROM python:3.12-slim

WORKDIR /app

# Primero solo requirements.txt, para aprovechar la caché de capas de Docker.
COPY requirements.txt requirements-dev.txt ./

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 8000
CMD ["sh", "entrypoint.sh"]