# tests/test_auth.py
import pytest
from httpx import AsyncClient
from app.database.mongo import user_collection
from app.utils.security import hash_password
from app.main import app


@pytest.mark.asyncio
async def test_register_user():
    # Test verisi
    user_data = {"email": "testuser@example.com", "password": "securepassword123"}

    # Yeni kullanıcıyı kaydetme isteği
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/register", json=user_data)

    # Yanıtın başarılı olduğunu kontrol et
    assert response.status_code == 200
    response_data = response.json()
    assert "email" in response_data
    assert "token" in response_data
    assert "refresh_token" in response_data
    assert response_data["email"] == user_data["email"]

    # Kullanıcı veritabanında oluşturulmuş mu kontrol et
    user_in_db = await user_collection.find_one({"email": user_data["email"]})
    assert user_in_db is not None
    assert user_in_db["email"] == user_data["email"]

    # Kullanıcının koleksiyonları oluşturuldu mu kontrol et
    collections = await user_collection.find({"user_id": user_in_db["_id"]}).to_list(
        length=100
    )
    assert (
        len(collections) > 0
    )  # En az 2 koleksiyon olmalı: İzlediklerim ve İzleyeceklerim
    assert any(col["name"] == "İzlediklerim" for col in collections)
    assert any(col["name"] == "İzleyeceklerim" for col in collections)
