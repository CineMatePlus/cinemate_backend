# --- BASE IMAGE ---
    FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

    ENV DEBIAN_FRONTEND=noninteractive \
        TZ=Etc/UTC \
        POETRY_VIRTUALENVS_CREATE=false \
        POETRY_NO_INTERACTION=1
    
    # Sistem gereksinimleri ve Poetry kurulumu
    RUN apt-get update && \
        apt-get install -y python3.10 python3-pip python-is-python3 git curl && \
        pip install poetry && \
        rm -rf /var/lib/apt/lists/*
    
    # Kullanıcı oluştur
    RUN useradd --create-home appuser
    WORKDIR /app
    COPY pyproject.toml poetry.lock* ./
    RUN poetry install --only main
    
    COPY ./app ./app
    RUN chown -R appuser:appuser /app
    COPY .env .env

    USER appuser
    
    EXPOSE 8080
    
    CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]

    
