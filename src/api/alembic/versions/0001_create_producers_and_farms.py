"""Migración inicial: crea las tablas `producers` y `farms`.

Escrita a mano. Los nombres de las restricciones (`op.f`) coinciden con la
convención de nombres de `app/db/models.py`.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "producers",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("document_number", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("municipality", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_producers")),
        sa.UniqueConstraint("document_number", name=op.f("uq_producers_document_number")),
    )
    
    op.create_table(
        "farms",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("producer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("geometry", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("area_ha", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "geometry->>'type' = 'Polygon'", name=op.f("ck_farms_geometry_is_polygon")
        ),
        sa.CheckConstraint("area_ha > 0", name=op.f("ck_farms_area_positive")),
        sa.ForeignKeyConstraint(
            ["producer_id"],
            ["producers.id"],
            name=op.f("fk_farms_producer_id_producers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_farms")),
        # UNIQUE en producer_id => relación uno a uno.
        sa.UniqueConstraint("producer_id", name=op.f("uq_farms_producer_id")),
    )
