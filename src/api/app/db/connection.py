"""Conexión a la base de datos: `engine`, `SessionLocal` y la dependencia `get_db`.

`get_db` se inyecta en los endpoints con `Depends(get_db)`: entrega una sesión
por petición y la cierra al terminar. La URL viene de la variable DATABASE_URL.
"""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por petición."""
    with SessionLocal() as db:
        yield db