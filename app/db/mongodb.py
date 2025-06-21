from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB]


async def init_db():
    """Veritabanı bağlantısını başlatır ve gerekli indeksleri oluşturur."""
    # User indexes
    await db.users.create_index("email", unique=True)

    # Movie indexes
    await db.movies.create_index([("title", "text"), ("overview", "text")])
    await db.movies.create_index("release_date")
    await db.movies.create_index("genres")

    # Collection indexes
    await db.collections.create_index("user_id")
    await db.collections.create_index([("user_id", 1), ("name", 1)], unique=True)
    
    # Comment indexes
    await db.comments.create_index("movie_id")
    await db.comments.create_index("user_id")

    # Interaction indexes
    await db.interactions.create_index(
        [("user_id", 1), ("movie_id", 1), ("interaction_type", 1)], unique=True
    )

def get_database():
    """Veritabanı bağlantısını döndürür"""
    return db
