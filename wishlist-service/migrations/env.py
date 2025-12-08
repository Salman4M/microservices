from sqlalchemy import create_engine, pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models import Wishlist
from sqlmodel import SQLModel

# Import all models above
target_metadata = SQLModel.metadata

url = os.getenv("DATABASE_URL") or context.config.get_main_option("sqlalchemy.url")
connectable = create_engine(url, poolclass=pool.NullPool)

def run_migrations_online():
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    # offline migrations
    url = os.getenv("DATABASE_URL") or context.config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
