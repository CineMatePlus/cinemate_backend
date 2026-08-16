from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.mongodb import init_db
from app.routes import auth, collection, comment, interaction, movie, user
from app.services.embedding import (
    EmbeddingProviderError,
    close_embedding_service,
    get_embedding_service,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API route'larını ekle
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(
    collection.router, prefix=f"{settings.API_V1_STR}/collections", tags=["collections"]
)
app.include_router(
    comment.router, prefix=f"{settings.API_V1_STR}/comments", tags=["comments"]
)
app.include_router(
    interaction.router,
    prefix=f"{settings.API_V1_STR}/interactions",
    tags=["User Interactions"],
)
app.include_router(user.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(
    movie.router, prefix=f"{settings.API_V1_STR}/movies", tags=["movies"]
)


@app.on_event("startup")
async def startup_event():
    """Uygulama başlatılırken çalışacak işlemler"""
    # Veritabanı bağlantısını ve indeksleri oluştur
    await init_db()
    if settings.EMBEDDING_WARMUP:
        await get_embedding_service().warmup()


@app.on_event("shutdown")
async def shutdown_event():
    await close_embedding_service()


@app.get("/")
async def root():
    return {"message": "Cinemate API'ye hoş geldiniz!"}


@app.get("/health/embedding")
async def embedding_health():
    try:
        health = await get_embedding_service().health()
        if not health.get("model_installed"):
            raise EmbeddingProviderError(
                f"Ollama is reachable, but model {settings.EMBEDDING_MODEL!r} "
                "is not installed."
            )
        return {"status": "healthy", **health}
    except EmbeddingProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
