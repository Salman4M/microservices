# Use Python slim image
FROM python:3.13-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV - the fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy ONLY dependency files first (better layer caching)
COPY pyproject.toml ./

# Install dependencies using UV from pyproject.toml
RUN uv pip install --system --no-cache .

# Copy entire project
COPY . .

# Copy entrypoint and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user and set permissions
RUN useradd -m appuser && chown -R appuser:appuser /app && chown appuser:appuser /entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Use entrypoint
ENTRYPOINT ["/entrypoint.sh"]