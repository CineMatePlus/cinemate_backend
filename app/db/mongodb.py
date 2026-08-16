from typing import Any

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
            indexes = (
                await target_db[collection_name]
                .list_search_indexes()
                .to_list(length=None)
            )
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
