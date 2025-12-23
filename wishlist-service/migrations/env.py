import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context
from dotenv import load_dotenv  # <--- Ensure python-dotenv is installed

# 1. Load environment variables from .env file
load_dotenv()

# 2. Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 3. Import your models
from sqlmodel import SQLModel

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4. OVERRIDE THE URL FROM .ENV
# This is the critical fix. We read the variable here in Python.
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is not set in .env file")

# Set the SQLAlchemy URL in the config object
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Create engine using the URL we set from env vars
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()