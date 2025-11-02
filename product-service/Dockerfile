# Use official Python 3.11 slim image
FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install pip and uv
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir uv

# Install project dependencies into .venv
RUN uv sync --frozen --no-dev

# Copy project code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI directly from venv (no rebuild of .venv each time)
CMD [".venv/bin/uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
