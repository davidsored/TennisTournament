FROM python:3.12.3-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    REFLEX_DIR=/app/.web

# Node.js 20 es necesario porque Reflex compila el frontend con Next.js.
# build-essential + libpq-dev compilan wheels nativos (psycopg2-binary, greenlet).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        curl \
        ca-certificates \
        gnupg \
        git \
        unzip \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

# Pre-descarga Bun y prepara .web/ para que el primer arranque no se demore.
RUN reflex init --template blank --loglevel warning || true

EXPOSE 3000 8000

CMD ["reflex", "run", "--env", "dev", "--backend-host", "0.0.0.0"]
