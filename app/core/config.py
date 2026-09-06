import os
from typing import List

from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()


def get_env(name: str, default: str) -> str:
    """Read settings from the process environment after loading .env defaults."""
    return os.getenv(name, default)


def get_bool_env(name: str, default: bool = False) -> bool:
    value = get_env(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}


class Settings:
    # Proje Bilgileri
    PROJECT_NAME: str = get_env("PROJECT_NAME", "Cinemate API")
    PROJECT_DESCRIPTION: str = get_env(
        "PROJECT_DESCRIPTION", "Cinemate API Documentation"
    )
    PROJECT_VERSION: str = get_env("PROJECT_VERSION", "1.0.0")
    API_V1_STR: str = get_env("API_V1_STR", "/api/v1")

    # CORS Ayarları
    CORS_ORIGINS: List[str] = [
        i.strip()
        for i in get_env(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
        ).split(",")
    ]
    CORS_ALLOW_CREDENTIALS: bool = get_bool_env("CORS_ALLOW_CREDENTIALS", True)
    if CORS_ALLOW_CREDENTIALS and "*" in CORS_ORIGINS:
        raise ValueError(
            "CORS_ORIGINS cannot contain '*' when CORS_ALLOW_CREDENTIALS=true."
        )

    # MongoDB Ayarları
    MONGODB_URL: str = get_env("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB: str = get_env("MONGODB_DB", "cinemate")

    # JWT Ayarları
    JWT_SECRET_KEY: str = get_env("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = get_env("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(get_env("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(get_env("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Güvenlik Ayarları
    PASSWORD_MIN_LENGTH: int = int(get_env("PASSWORD_MIN_LENGTH", "8"))
    PASSWORD_MAX_LENGTH: int = int(get_env("PASSWORD_MAX_LENGTH", "32"))

    # Embedding service
    EMBEDDING_PROVIDER: str = get_env("EMBEDDING_PROVIDER", "ollama")
    EMBEDDING_BASE_URL: str = get_env(
        "EMBEDDING_BASE_URL", "http://localhost:11434"
    ).rstrip("/")
    EMBEDDING_MODEL: str = get_env("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    EMBEDDING_DIMENSIONS: int = int(get_env("EMBEDDING_DIMENSIONS", "1024"))
    EMBEDDING_TIMEOUT_SECONDS: float = float(
        get_env("EMBEDDING_TIMEOUT_SECONDS", "120")
    )
    EMBEDDING_BATCH_SIZE: int = int(get_env("EMBEDDING_BATCH_SIZE", "64"))
    EMBEDDING_KEEP_ALIVE: str = get_env("EMBEDDING_KEEP_ALIVE", "30m")
    EMBEDDING_WARMUP: bool = get_bool_env("EMBEDDING_WARMUP", False)
    EMBEDDING_QUERY_CACHE_SIZE: int = int(get_env("EMBEDDING_QUERY_CACHE_SIZE", "512"))
    EMBEDDING_QUERY_CACHE_TTL_SECONDS: float = float(
        get_env("EMBEDDING_QUERY_CACHE_TTL_SECONDS", "600")
    )
    EMBEDDING_QUERY_PREFIX: str = get_env(
        "EMBEDDING_QUERY_PREFIX",
        "Instruct: Retrieve movie and TV show descriptions relevant to the user query.\\nQuery: ",
    )
    MOVIE_VECTOR_INDEX: str = get_env("MOVIE_VECTOR_INDEX", "movie_vector_index")
    USER_VECTOR_INDEX: str = get_env("USER_VECTOR_INDEX", "user_vector_index")

    # Vector search performance and observability
    VECTOR_SEARCH_CANDIDATE_MULTIPLIER: int = int(
        get_env("VECTOR_SEARCH_CANDIDATE_MULTIPLIER", "20")
    )
    VECTOR_SEARCH_MIN_CANDIDATES: int = int(
        get_env("VECTOR_SEARCH_MIN_CANDIDATES", "100")
    )
    VECTOR_SEARCH_MAX_CANDIDATES: int = int(
        get_env("VECTOR_SEARCH_MAX_CANDIDATES", "1000")
    )
    VECTOR_SEARCH_METRICS_WINDOW: int = int(
        get_env("VECTOR_SEARCH_METRICS_WINDOW", "100")
    )
    VECTOR_SEARCH_STARTUP_CHECK: bool = get_bool_env(
        "VECTOR_SEARCH_STARTUP_CHECK", True
    )


settings = Settings()
