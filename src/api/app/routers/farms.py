"""Endpoints de la finca de un productor: subir el GeoJSON y consultarlo.

- POST: recibe un archivo GeoJSON, lo valida (422 con mensaje claro si falla),
  calcula el área y guarda la finca. Cada productor tiene una sola finca (409
  si ya tiene).
- GET: devuelve la finca como Feature GeoJSON con `name` y `area_ha`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Farm, Producer
from app.db.connection import get_db
from app.schemas import FarmFeature, FarmProperties
from app.services.geo import GeoJSONError, parse_farm_geojson

DbSession = Annotated[Session, Depends(get_db)]
router = APIRouter(prefix="/producers/{producer_id}/farm", tags=["farms"])

def get_producer(db: Session, producer_id: int) -> Producer:
    producer = db.get(Producer, producer_id)
    
    if producer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Productor no encontrado")

    return producer

def to_feature(farm: Farm) -> FarmFeature:
    return FarmFeature(
        geometry=farm.geometry,
        properties=FarmProperties(name=farm.name, area_ha=farm.area_ha),
    )

@router.post("", response_model=FarmFeature, status_code=status.HTTP_201_CREATED)
def upload_farm(
    producer_id: int,
    db: DbSession,
    file: Annotated[UploadFile, File(description="Archivo .geojson con el polígono")],
    name: Annotated[str | None, Form(max_length=200)] = None,
):
    """Sube el GeoJSON de la finca. El nombre sale del campo `name`, de
    `properties.name` del GeoJSON o, en su defecto, de "Finca de <productor>"."""
    producer = get_producer(db, producer_id)
    
    if producer.farm is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El productor ya tiene una finca registrada")

    raw = file.file.read()

    try:
        parsed = parse_farm_geojson(raw)
    except GeoJSONError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from None

    farm = Farm(
        producer_id=producer.id,
        name=(name or "").strip() or parsed.name or f"Finca de {producer.full_name}"[:200],
        geometry=parsed.geometry,
        area_ha=parsed.area_ha,
    )

    db.add(farm)
    db.commit()

    return to_feature(farm)

@router.get("", response_model=FarmFeature)
def get_farm(producer_id: int, db: DbSession):
    """Devuelve la finca del productor como Feature GeoJSON."""
    producer = get_producer(db, producer_id)

    if producer.farm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El productor no tiene finca registrada")
        
    return to_feature(producer.farm)