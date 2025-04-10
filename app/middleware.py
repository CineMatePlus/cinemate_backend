from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.security import decode_access_token
from app.database.mongo import user_collection


class TokenValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # İsteğin yoluna göre işlem yap
        if request.url.path not in ["/auth/login", "/auth/register"]:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Token missing or invalid")

            token = auth_header.split(" ")[1]
            try:
                payload = decode_access_token(token)  # Token'dan payload'ı al
                email = payload.get("sub")  # Token'dan email almak

                if not email:
                    raise HTTPException(
                        status_code=401, detail="Email not found in token"
                    )

                # Email ile kullanıcıyı sorgula
                user = await user_collection.find_one({"email": email})
                if not user:
                    raise HTTPException(status_code=401, detail="User not found")

                # Kullanıcıyı request.state.user'e ekle
                request.state.user = user

            except Exception as e:
                raise HTTPException(
                    status_code=401, detail="Invalid token or user not found"
                )

        response = await call_next(request)
        return response
