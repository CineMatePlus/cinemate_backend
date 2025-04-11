from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    # Proje Bilgileri
    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str
    PROJECT_VERSION: str
    API_V1_STR: str

    # CORS Ayarları
    CORS_ORIGINS: List[AnyHttpUrl]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # MongoDB Ayarları
    MONGODB_URL: str
    MONGODB_DB: str

    # JWT Ayarları
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Güvenlik Ayarları
    PASSWORD_MIN_LENGTH: int
    PASSWORD_MAX_LENGTH: int

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "validate_by_name": True,
    }


settings = Settings()
