"""Create the MongoDB Vector Search indexes required by CineMate."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import AutoReconnect, OperationFailure
from pymongo.operations import SearchIndexModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from app.core.config import settings  # noqa: E402

INDEXES = (
    ("movies", settings.MOVIE_VECTOR_INDEX),
    ("users", settings.USER_VECTOR_INDEX),
)
DEFINITION: dict[str, Any] = {
    "fields": [
        {
            "type": "vector",
            "path": "embedding",
            "numDimensions": settings.EMBEDDING_DIMENSIONS,
            "similarity": "cosine",
        }
    ]
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create CineMate vector indexes on Atlas or Atlas Local."
    )
    parser.add_argument("--mongo-url", default=None)
    parser.add_argument("--database", default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print index definitions without connecting to MongoDB.",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait until every required search index reports READY.",
    )
    parser.add_argument(
        "--wait-timeout",
        type=float,
        default=180.0,
        help="Maximum seconds to wait for search indexes (default: 180).",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds between readiness checks (default: 2).",
    )
    return parser.parse_args()


def search_indexes(collection: Any, *, deadline: float, poll_interval: float, **kwargs):
    """Atlas Local can answer ping before its search management service is ready."""
    while True:
        try:
            return list(collection.list_search_indexes(**kwargs))
        except (AutoReconnect, OperationFailure) as exc:
            transient = isinstance(exc, AutoReconnect) or (
                exc.code == 125
                and "Error connecting to Search Index Management service" in str(exc)
            )
            if not transient:
                raise
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    "Search index management service did not become ready"
                ) from exc
            time.sleep(min(poll_interval, max(0, deadline - time.monotonic())))


def wait_until_ready(database: Any, *, timeout: float, poll_interval: float) -> None:
    deadline = time.monotonic() + timeout
    pending = {collection_name: index_name for collection_name, index_name in INDEXES}
    while pending:
        for collection_name, index_name in tuple(pending.items()):
            indexes = search_indexes(
                database[collection_name],
                deadline=deadline,
                poll_interval=poll_interval,
                name=index_name,
            )
            index = indexes[0] if indexes else None
            status = str(index.get("status", "MISSING")).upper() if index else "MISSING"
            queryable = bool(index.get("queryable", False)) if index else False
            if status == "READY" and queryable:
                print(f"{database.name}.{collection_name}: {index_name} is READY.")
                pending.pop(collection_name)
        if not pending:
            return
        if time.monotonic() >= deadline:
            names = ", ".join(
                f"{collection}.{index}" for collection, index in pending.items()
            )
            raise TimeoutError(f"Timed out waiting for Vector Search indexes: {names}")
        time.sleep(poll_interval)


def main() -> None:
    args = parse_args()
    load_dotenv(PROJECT_ROOT / ".env")

    if args.dry_run:
        for collection_name, index_name in INDEXES:
            print(
                json.dumps(
                    {
                        "collection": collection_name,
                        "name": index_name,
                        "type": "vectorSearch",
                        "definition": DEFINITION,
                    },
                    indent=2,
                )
            )
        return

    mongo_url = args.mongo_url or os.getenv("MONGODB_URL")
    database_name = args.database or os.getenv("MONGODB_DB", "cinemate")
    if not mongo_url:
        raise RuntimeError("MONGODB_URL must point to Atlas or Atlas Local.")

    client = MongoClient(mongo_url, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
        database = client[database_name]
        deadline = time.monotonic() + args.wait_timeout
        existing_collections = set(database.list_collection_names())
        for collection_name, index_name in INDEXES:
            if collection_name not in existing_collections:
                database.create_collection(collection_name)
                existing_collections.add(collection_name)
                print(f"{database_name}.{collection_name}: created empty collection.")
            collection = database[collection_name]
            existing = {
                index.get("name")
                for index in search_indexes(
                    collection, deadline=deadline, poll_interval=args.poll_interval
                )
            }
            if index_name in existing:
                print(
                    f"{database_name}.{collection_name}: {index_name} already exists."
                )
                continue
            created_name = collection.create_search_index(
                model=SearchIndexModel(
                    definition=DEFINITION,
                    name=index_name,
                    type="vectorSearch",
                )
            )
            print(
                f"{database_name}.{collection_name}: requested {created_name}. "
                "Wait for the index status to become READY before vector queries."
            )
        if args.wait:
            wait_until_ready(
                database,
                timeout=args.wait_timeout,
                poll_interval=args.poll_interval,
            )
    finally:
        client.close()


if __name__ == "__main__":
    main()
