import inspect
from typing import Any

from pymongo import ASCENDING, AsyncMongoClient

from app.core.config import settings

_client: AsyncMongoClient | None = None
_database: Any = None


class DatabaseProxy:
    """Resolve the active database lazily after the application lifespan starts."""

    def __getitem__(self, name: str) -> Any:
        if _database is None:
            raise RuntimeError("MongoDB has not been connected yet.")
        return _database[name]

    def __getattr__(self, name: str) -> Any:
        if _database is None:
            raise RuntimeError("MongoDB has not been connected yet.")
        return getattr(_database, name)


db = DatabaseProxy()


async def connect_database() -> None:
    global _client, _database
    if _client is not None:
        return
    client = AsyncMongoClient(
        settings.MONGODB_URL, serverSelectionTimeoutMS=10_000, tz_aware=True
    )
    try:
        await client.admin.command("ping")
    except Exception:
        await client.close()
        raise
    _client = client
    _database = client[settings.MONGODB_DB]


async def close_database() -> None:
    global _client, _database
    client = _client
    _client = None
    _database = None
    if client is not None:
        await client.close()


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

    # Refresh-token session indexes
    await db.refresh_sessions.create_index("token_hash", unique=True)
    await db.refresh_sessions.create_index("jti", unique=True)
    await db.refresh_sessions.create_index("family_id")
    await db.refresh_sessions.create_index("user_id")
    await db.refresh_sessions.create_index(
        [("expires_at", ASCENDING)], expireAfterSeconds=0
    )


class VectorSearchIndexNotReadyError(RuntimeError):
    """One or more required Atlas Search indexes cannot serve queries yet."""


async def inspect_vector_search_indexes(database: Any = None) -> list[dict[str, Any]]:
    """Return the current state of every vector index required by the API."""
    target_db = db if database is None else database
    required = (
        ("movies", settings.MOVIE_VECTOR_INDEX),
        ("users", settings.USER_VECTOR_INDEX),
    )
    results: list[dict[str, Any]] = []
    for collection_name, index_name in required:
        try:
            cursor = target_db[collection_name].list_search_indexes()
            if inspect.isawaitable(cursor):
                cursor = await cursor
            indexes = await cursor.to_list(length=None)
            index = next(
                (item for item in indexes if item.get("name") == index_name), None
            )
            status = str(index.get("status", "MISSING")).upper() if index else "MISSING"
            results.append(
                {
                    "collection": collection_name,
                    "index": index_name,
                    "status": status,
                    "queryable": (
                        bool(index.get("queryable", False)) if index else False
                    ),
                    "ready": status == "READY",
                }
            )
        except Exception as exc:
            results.append(
                {
                    "collection": collection_name,
                    "index": index_name,
                    "status": "ERROR",
                    "queryable": False,
                    "ready": False,
                    "error": str(exc),
                }
            )
    return results


async def verify_vector_search_indexes_ready(database: Any = None) -> None:
    """Fail startup early instead of discovering a missing index on the first request."""
    statuses = await inspect_vector_search_indexes(database)
    unavailable = [item for item in statuses if not item["ready"]]
    if unavailable:
        details = "; ".join(
            f"{item['collection']}.{item['index']}={item['status']}"
            + (f" ({item['error']})" if item.get("error") else "")
            for item in unavailable
        )
        raise VectorSearchIndexNotReadyError(
            "Required vector search indexes are not READY: " + details
        )


def get_database():
    """Veritabanı bağlantısını döndürür"""
    return db
