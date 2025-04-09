from fastapi import APIRouter, HTTPException, Depends, Request
from app.models.user_model import UserIn, UserInDB, UserOut
from app.database.mongo import user_collection
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.security import (
    ALGORITHM,
    SECRET_KEY,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    create_refresh_token,
)

auth_router = APIRouter()


@auth_router.post("/register", response_model=UserOut)
async def register(user: UserIn):
    # Kullanıcı zaten var mı kontrol edelim
    if await user_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Şifreyi hashleyelim
    hashed_pw = hash_password(user.password)

    # Yeni kullanıcıyı veritabanına ekleyelim
    new_user = UserInDB(
        email=user.email,
        hashed_password=hashed_pw,
        collections=[],  # Başlangıçta boş koleksiyon listesi
    )

    # Varsayılan koleksiyonları ekle
    new_user.add_default_collections()

    # Kullanıcıyı veritabanına kaydet
    await user_collection.insert_one(new_user.dict(exclude_unset=True))

    # Token oluştur
    token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    return {"email": user.email, "token": token, "refresh_token": refresh_token}


@auth_router.post("/login", response_model=UserOut)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username # form_data.username yerine form_data.email kullanılmalı
    password = form_data.password
    db_user = await user_collection.find_one({"email": email})
    if not db_user or not verify_password(password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": email})
    refresh_token = create_refresh_token({"sub": email})
    return {"access_token": access_token, "refresh_token": refresh_token}


@auth_router.get("/me")
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}


@auth_router.post("/refresh")
async def refresh_token(request: Request):
    body = await request.json()
    token = body.get("refresh_token")

    if not token:
        raise HTTPException(status_code=400, detail="Refresh token missing")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token({"sub": email})
    return {"token": new_access_token}
