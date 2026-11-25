"""Esquemas Pydantic de la API, con entrada y salida separadas.

- `ProducerCreate`: lo que envía el cliente al crear un productor. Solo admite
  los campos permitidos (rechaza `id`, `created_at`, etc.) y recorta espacios.
- `ProducerOut` / `FarmOut`: lo que devuelve la API al listar productores.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

class ProducerCreate(BaseModel):
    """Entrada: datos para crear un productor (longitudes iguales a las de la BD)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    document_number: str = Field(min_length=1, max_length=32)
    full_name: str = Field(min_length=1, max_length=200)
    municipality: str = Field(min_length=1, max_length=100)

class ProducerOut(BaseModel):
    """Salida: productor con el resumen de su finca (o `null` si aún no tiene)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    document_number: str
    full_name: str
    municipality: str
    created_at: datetime
    farm: FarmOut | None
