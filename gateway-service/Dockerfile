FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and lock file first
COPY pyproject.toml uv.lock ./

# Install Python dependencies from pyproject.toml
RUN pip install --upgrade pip
RUN pip install .

# Copy application 
COPY gateway/ /app/gateway

# Copy entrypoint script and make executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for Cloud Run
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]