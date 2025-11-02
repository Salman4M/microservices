# Use Python slim image
FROM python:3.13-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PORT 8000

# Set working directory
WORKDIR /app

# Install system dependencies for Postgres client and psql
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and lock file first
COPY pyproject.toml uv.lock ./

# Install Python dependencies from pyproject.toml
RUN pip install --upgrade pip
RUN pip install .

# Copy Alembic configs
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

# Copy application source code
COPY src/ /app/src

# Copy entrypoint script and make executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for Cloud Run
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
