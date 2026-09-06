import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError, OperationFailure

from app.core.config import settings
from app.db.mongodb import (
    close_database,
    connect_database,
    get_database,
    init_db,
    inspect_vector_search_indexes,
    verify_vector_search_indexes_ready,
)
from app.routes import auth, collection, comment, interaction, movie, user
from app.services.embedding import (
    EmbeddingProviderError,
    close_embedding_service,
    get_embedding_service,
)
from app.services.vector_search import vector_search_metrics


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_database()
    try:
        await init_db()
        if settings.VECTOR_SEARCH_STARTUP_CHECK:
            await verify_vector_search_indexes_ready()
        if settings.EMBEDDING_WARMUP:
            await get_embedding_service().warmup()
        yield
    finally:
        await close_embedding_service()
        await close_database()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
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


@app.get("/")
async def root():
    return {"message": "Cinemate API'ye hoş geldiniz!"}


@app.get("/health/live")
async def liveness_health():
    return {"status": "healthy"}


@app.get("/health/ready")
async def readiness_health():
    try:
        await get_database().command("ping")
        indexes = await inspect_vector_search_indexes()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "reason": type(exc).__name__},
        ) from exc
    if not all(index["ready"] for index in indexes):
        public_indexes = [
            {
                key: index[key]
                for key in ("collection", "index", "status", "queryable", "ready")
            }
            for index in indexes
        ]
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "indexes": public_indexes},
        )
    return {"status": "healthy", "indexes": indexes}


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


@app.get("/health/vector-search")
async def vector_search_health():
    indexes = await inspect_vector_search_indexes()
    if not all(index["ready"] for index in indexes):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "indexes": indexes},
        )
    return {"status": "healthy", "indexes": indexes}


@app.get("/metrics/vector-search")
async def vector_search_measurements():
    return vector_search_metrics.snapshot()


@app.exception_handler(DuplicateKeyError)
async def duplicate_key_error(request, exc):
    return JSONResponse(status_code=409, content={"detail": "Bu kayıt zaten mevcut."})


@app.exception_handler(OperationFailure)
async def database_operation_error(request, exc):
    logging.getLogger(__name__).exception("Database operation failed", exc_info=exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "Veri servisi geçici olarak kullanılamıyor."},
    )
