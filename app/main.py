from fastapi import FastAPI
from app.routes import auth, content
from app.middleware import TokenValidationMiddleware

app = FastAPI()
app.add_middleware(TokenValidationMiddleware)

app.include_router(auth.auth_router, prefix="/auth", tags=["auth"])
app.include_router(content.content_router)
