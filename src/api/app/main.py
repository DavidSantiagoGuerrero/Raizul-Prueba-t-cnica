"""Punto de entrada de la API: crea la app FastAPI y registra los routers.

Se ejecuta con `uvicorn app.main:app`. La documentación interactiva queda en `/docs`.
"""

from fastapi import FastAPI

from app.routers import producers

app = FastAPI(title="API de productores de cacao")
app.include_router(producers.router)

@app.get("/health", tags=["health"])
def health():
    """Comprobación de vida del servicio."""
    return {"status": "ok"}