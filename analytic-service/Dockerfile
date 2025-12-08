# Base image
FROM python:3.11-slim

# İş qovluğu
WORKDIR /app

# Sistem paketləri
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# pip güncəllə
RUN pip install --upgrade pip --default-timeout=100

# Layihə fayllarını kopyala
COPY . .

# Python dependencies
RUN pip install --no-cache-dir --default-timeout=100 --retries=5 -r requirements.txt

# Ətraf mühit dəyişənləri
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV ENV=DEPLOY
ENV DOCKER=1

# Port expose
EXPOSE ${PORT}

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
