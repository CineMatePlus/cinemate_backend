from typing import List
from dotenv import load_dotenv, dotenv_values

# .env dosyasını yükle
load_dotenv()
env = dotenv_values()


class Settings:
    # Proje Bilgileri
    PROJECT_NAME: str = env.get("PROJECT_NAME", "Cinemate API")
    PROJECT_DESCRIPTION: str = env.get(
        "PROJECT_DESCRIPTION", "Cinemate API Documentation"
    )
    PROJECT_VERSION: str = env.get("PROJECT_VERSION", "1.0.0")
    API_V1_STR: str = env.get("API_V1_STR", "/api/v1")

    # CORS Ayarları
    CORS_ORIGINS: List[str] = [
        i.strip() for i in env.get("CORS_ORIGINS", "*").split(",")
    ]

    # MongoDB Ayarları
    MONGODB_URL: str = env.get("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB: str = env.get("MONGODB_DB", "cinemate")

    # JWT Ayarları
    JWT_SECRET_KEY: str = env.get("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = env.get("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(env.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(env.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Güvenlik Ayarları
    PASSWORD_MIN_LENGTH: int = int(env.get("PASSWORD_MIN_LENGTH", "8"))
    PASSWORD_MAX_LENGTH: int = int(env.get("PASSWORD_MAX_LENGTH", "32"))


settings = Settings()
