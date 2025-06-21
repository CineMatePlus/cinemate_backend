from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routes import auth, collection, comment, interaction, movie, user
from app.db.mongodb import init_db

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
app.include_router(
    user.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"]
)
app.include_router(
    movie.router, prefix=f"{settings.API_V1_STR}/movies", tags=["movies"]
)


@app.on_event("startup")
async def startup_event():
    """Uygulama başlatılırken çalışacak işlemler"""
    # Veritabanı bağlantısını ve indeksleri oluştur
    await init_db()


@app.get("/")
async def root():
    return {"message": "Cinemate API'ye hoş geldiniz!"}
