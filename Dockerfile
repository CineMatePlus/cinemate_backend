# Stage 1: Builder - Geliştirme araçları burada
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04 AS builder

ENV TZ=Etc/UTC
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y python3.10 python3-pip python-is-python3 git curl && \
    rm -rf /var/lib/apt/lists/*

# Poetry kur
RUN pip install poetry

# Projeyi kopyala ve bağımlılıkları kur
WORKDIR /app
COPY pyproject.toml poetry.lock* poetry.toml ./

# Poetry'nin sanal ortam oluşturmasına izin ver ve bağımlılıkları kur
RUN poetry install --without dev --no-interaction --no-ansi


# Stage 2: Runtime - Hafif CUDA + sadece çalışan bağımlılıklar
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV TZ=Etc/UTC
ENV DEBIAN_FRONTEND=noninteractive

# Python ve sistem gereksinimleri
RUN apt-get update && \
    apt-get install -y python3.10 python-is-python3 && \
    rm -rf /var/lib/apt/lists/*

# Kullanıcı oluştur
RUN useradd --create-home appuser
WORKDIR /app
RUN chown appuser:appuser /app

# Gerekli bağımlılıkları kopyala (sanal ortamdan)
COPY --from=builder /app/.venv/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /app/.venv/bin /usr/local/bin

# Uygulama kodunu kopyala
COPY --chown=appuser:appuser ./app ./app

# Non-root kullanıcıya geç
USER appuser

# Cloud Run uyumu için 8080
EXPOSE 8080

# Uvicorn ile FastAPI'yi çalıştır
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
