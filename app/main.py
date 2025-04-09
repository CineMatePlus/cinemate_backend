from fastapi import FastAPI
from app.routes import auth, content

app = FastAPI()

app.include_router(auth.auth_router, prefix="/auth", tags=["auth"])
app.include_router(content.content_router)
