"""Endpoints de productores: crear y listar.

La sesión de base de datos se inyecta con `Depends(get_db)`. Los endpoints son
síncronos (`def`): FastAPI los ejecuta en un hilo, lo que encaja con la sesión
síncrona de SQLAlchemy.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Producer
from app.db.connection import get_db
from app.schemas import ProducerCreate, ProducerOut

DbSession = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/producers", tags=["producers"])

@router.post("", response_model=ProducerOut, status_code=status.HTTP_201_CREATED)
def create_producer(payload: ProducerCreate, db: DbSession):
    """Crea un productor. Responde 409 si el documento ya existe."""
    existing = db.query(Producer).filter(
        Producer.document_number == payload.document_number
    ).first()

    if (existing):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya existe un productor con ese número de documento",
        )

    producer = Producer(**payload.model_dump())
    db.add(producer)
    db.commit()


@router.get("", response_model=list[ProducerOut])
def list_producers(db: DbSession):
    """Lista los productores con el resumen de su finca (si la tienen)."""
    return db.scalars(select(Producer).order_by(Producer.id)).all()