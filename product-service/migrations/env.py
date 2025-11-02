import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# --------------------------------------------------------
# Make 'src' folder importable
# --------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# --------------------------------------------------------
# Load environment variables from .env
# --------------------------------------------------------
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
print("Loading .env from:", dotenv_path)
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL =", DATABASE_URL)

# --------------------------------------------------------
# Alembic config
# --------------------------------------------------------
config = context.config

# Override sqlalchemy.url in alembic.ini with .env value
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --------------------------------------------------------
# Import SQLAlchemy Base and all models
# --------------------------------------------------------
from app.core.db import Base  # your declarative base

# Import all models so Base.metadata includes them
from app.models.v1.product import Product
from app.models.v1.product_variation import ProductVariation
from app.models.v1.product_image import ProductImage
from app.models.v1.product_category import ProductCategory
from app.models.v1.comment import Comment
from app.models.v1.category import Category

# Target metadata for autogenerate (after all imports)
target_metadata = Base.metadata

# --------------------------------------------------------
# Debug: check what tables Alembic sees
# --------------------------------------------------------
print("Tables detected by Alembic:", target_metadata.tables.keys())

# --------------------------------------------------------
# Migration functions
# --------------------------------------------------------
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
