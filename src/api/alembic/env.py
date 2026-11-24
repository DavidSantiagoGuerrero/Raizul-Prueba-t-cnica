"""Entorno de Alembic: conecta las migraciones con los modelos y la URL de la app.

Usa `Base.metadata` como metadata objetivo y la `DATABASE_URL` de la aplicación.
Soporta modo offline (`--sql`) y online.
"""

from alembic import context
from sqlalchemy import create_engine

from app.db.models import Base
from app.db.connection import DATABASE_URL

target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(DATABASE_URL).connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()