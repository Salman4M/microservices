# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev ca-certificates postgresql-client && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pyproject.toml
COPY pyproject.toml ./ 

# Generate requirements.txt from pyproject.toml
RUN python -c "import tomllib, sys; data=tomllib.load(open('pyproject.toml','rb')); reqs=data.get('project', {}).get('dependencies', []); open('requirements.txt','w',encoding='utf-8').write('\n'.join(reqs)); print(f'Wrote {len(reqs)} dependencies to requirements.txt', file=sys.stderr)"

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Change to Django project directory
WORKDIR /app/shop_service

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app

# Copy and make entrypoint.sh executable as root
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER appuser

# Create static and media directories with proper permissions
RUN mkdir -p /app/staticfiles /app/shop_service/media
RUN chown -R appuser:appuser /app/staticfiles /app/shop_service/media

# Expose port
ENV PORT 8000
EXPOSE 8000

# Use entrypoint.sh to run migrations, collectstatic, and start Gunicorn
CMD ["/app/entrypoint.sh"]