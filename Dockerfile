# === BASE IMAGE ===
FROM python:3.10-slim as base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    TZ=Etc/UTC

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry yükle
RUN pip install --upgrade pip \
    && pip install poetry

# === BUILD STAGE ===
FROM base as builder

WORKDIR /app

# Poetry config ve bağımlılıklar
COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main

# Hugging Face modeli indir
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

# === RUNTIME STAGE ===
FROM base as runtime

# Kullanıcı oluştur
RUN useradd --create-home appuser
WORKDIR /app

# Uygulama dosyalarını kopyala
COPY --from=builder /app /app
COPY ./app ./app
COPY .env .env

# HuggingFace cache klasörünü kopyala
COPY --from=builder /root/.cache /root/.cache

# Dosya izinleri
RUN chown -R appuser:appuser /app /root/.cache
USER appuser

# Cloud Run port
EXPOSE 8080

# Başlatıcı komut
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
