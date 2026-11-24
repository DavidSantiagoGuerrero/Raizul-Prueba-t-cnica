"""Modelos ORM (SQLAlchemy 2.x): `Producer` (producers) y `Farm` (farms).

Relación uno a uno: el UNIQUE sobre `farms.producer_id` impide una segunda
finca por productor. La geometría se guarda como GeoJSON (solo el objeto
`Polygon`) en una columna JSONB; `area_ha` la calcula el servidor.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    MetaData,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """Base declarativa. La convención da nombres estables a las restricciones."""

    metadata = MetaData(
        naming_convention={
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

class Producer(Base):
    """Productor de cacao; `document_number` es único."""

    __tablename__ = "producers"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    document_number: Mapped[str] = mapped_column(String(32), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    municipality: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Puede no tener finca todavía (el GeoJSON se sube después).
    farm: Mapped["Farm | None"] = relationship(
        back_populates="producer",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

class Farm(Base):
    """Finca del productor: nombre, polígono GeoJSON y área en hectáreas."""

    __tablename__ = "farms"
    __table_args__ = (
        CheckConstraint("geometry->>'type' = 'Polygon'", name="geometry_is_polygon"),
        CheckConstraint("area_ha > 0", name="area_positive"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    producer_id: Mapped[int] = mapped_column(
        ForeignKey("producers.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(String(200))
    geometry: Mapped[dict[str, Any]] = mapped_column(JSONB)
    area_ha: Mapped[float]

    producer: Mapped[Producer] = relationship(back_populates="farm")