from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB]


async def init_db():
    """Veritabanı bağlantısını başlatır ve gerekli indeksleri oluşturur"""
    # Kullanıcı indeksleri
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True, sparse=True)
    await db.users.create_index("gender")

    # İçerik indeksleri
    await db.contents.create_index("title")
    await db.contents.create_index("type")
    await db.contents.create_index("created_at")
    # Text search için index
    await db.contents.create_index([("title", "text"), ("description", "text")])

    # Koleksiyon indeksleri
    await db.collections.create_index("user_id")
    await db.collections.create_index([("user_id", 1), ("title", 1)], unique=True)
    await db.collections.create_index("content_ids")
    await db.collections.create_index("created_at")

    # Yorum indeksleri
    await db.comments.create_index("content_id")
    await db.comments.create_index("user_id")
    await db.comments.create_index("created_at")

    # Kullanıcı-İçerik ilişki indeksleri
    await db.user_contents.create_index(
        [("user_id", 1), ("content_id", 1)], unique=True
    )
    await db.user_contents.create_index("status")
    await db.user_contents.create_index("rating")
    await db.user_contents.create_index("created_at")


def get_database():
    """Veritabanı bağlantısını döndürür"""
    return db
