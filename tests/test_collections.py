import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.collection import CollectionCreate, CollectionUpdate
from app.models.user import UserCreate
from app.models.content import ContentCreate

client = TestClient(app)

# Test için gerekli veriler
test_user = UserCreate(
    email="test@example.com", username="testuser", password="testpassword123"
)

test_content = ContentCreate(
    title="Test Content",
    description="Test Description",
    type="movie",
    release_date="2024-01-01",
    duration=120,
    rating=8.5,
    genres=["Action", "Adventure"],
    cast=["Actor 1", "Actor 2"],
    director="Test Director",
    poster_url="https://example.com/poster.jpg",
    trailer_url="https://example.com/trailer.mp4",
)

test_collection = CollectionCreate(
    title="Test Collection", description="Test Collection Description", is_public=True
)


@pytest.fixture
async def auth_token():
    """Test için auth token oluşturur"""
    # Kullanıcı oluştur
    response = client.post("/api/auth/register", json=test_user.dict())
    assert response.status_code == 201

    # Giriş yap ve token al
    response = client.post(
        "/api/auth/login",
        data={"username": test_user.email, "password": test_user.password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def content_id(auth_token):
    """Test için içerik oluşturur"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/api/contents/", json=test_content.dict(), headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


def test_create_collection(auth_token):
    """Koleksiyon oluşturma testi"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post(
        "/api/collections/", json=test_collection.dict(), headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == test_collection.title
    assert data["description"] == test_collection.description
    assert data["is_public"] == test_collection.is_public
    return data["id"]


def test_get_collections(auth_token):
    """Koleksiyonları listeleme testi"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/collections/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_collection(auth_token):
    """Koleksiyon detayı getirme testi"""
    collection_id = test_create_collection(auth_token)
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get(f"/api/collections/{collection_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == collection_id


def test_update_collection(auth_token):
    """Koleksiyon güncelleme testi"""
    collection_id = test_create_collection(auth_token)
    headers = {"Authorization": f"Bearer {auth_token}"}

    update_data = CollectionUpdate(
        title="Updated Title", description="Updated Description", is_public=False
    )

    response = client.put(
        f"/api/collections/{collection_id}",
        json=update_data.dict(exclude_unset=True),
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data.title
    assert data["description"] == update_data.description
    assert data["is_public"] == update_data.is_public


def test_delete_collection(auth_token):
    """Koleksiyon silme testi"""
    collection_id = test_create_collection(auth_token)
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = client.delete(f"/api/collections/{collection_id}", headers=headers)
    assert response.status_code == 200

    # Silinen koleksiyonu getirmeye çalış
    response = client.get(f"/api/collections/{collection_id}", headers=headers)
    assert response.status_code == 404


def test_add_content_to_collection(auth_token, content_id):
    """Koleksiyona içerik ekleme testi"""
    collection_id = test_create_collection(auth_token)
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = client.post(
        f"/api/collections/{collection_id}/contents/{content_id}", headers=headers
    )
    assert response.status_code == 200

    # Koleksiyonun içeriğini kontrol et
    response = client.get(f"/api/collections/{collection_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert content_id in data["content_ids"]


def test_remove_content_from_collection(auth_token, content_id):
    """Koleksiyondan içerik çıkarma testi"""
    collection_id = test_create_collection(auth_token)
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Önce içerik ekle
    client.post(
        f"/api/collections/{collection_id}/contents/{content_id}", headers=headers
    )

    # Sonra içeriği çıkar
    response = client.delete(
        f"/api/collections/{collection_id}/contents/{content_id}", headers=headers
    )
    assert response.status_code == 200

    # Koleksiyonun içeriğini kontrol et
    response = client.get(f"/api/collections/{collection_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert content_id not in data["content_ids"]


def test_get_user_public_collections(auth_token):
    """Kullanıcının public koleksiyonlarını getirme testi"""
    # Public koleksiyon oluştur
    collection = CollectionCreate(
        title="Public Collection",
        description="Public Collection Description",
        is_public=True,
    )
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/api/collections/", json=collection.dict(), headers=headers)
    assert response.status_code == 201
    user_id = response.json()["user_id"]

    # Public koleksiyonları getir
    response = client.get(f"/api/collections/user/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(collection["is_public"] for collection in data)
