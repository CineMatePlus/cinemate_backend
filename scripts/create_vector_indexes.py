"""Create the Atlas Vector Search indexes required by CineMate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EMBEDDING_DIMENSIONS = 1024
INDEXES = (
    ("movies", "vector_index"),
    ("users", "user_vector_index"),
)
DEFINITION: dict[str, Any] = {
    "fields": [
        {
            "type": "vector",
            "path": "embedding",
            "numDimensions": EMBEDDING_DIMENSIONS,
            "similarity": "cosine",
        }
    ]
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create CineMate vector indexes on a MongoDB Atlas database."
    )
    parser.add_argument("--mongo-url", default=None)
    parser.add_argument("--database", default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print index definitions without connecting to Atlas.",
    )
    return parser.parse_args()


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
        raise RuntimeError("MONGODB_URL must point to a MongoDB Atlas deployment.")

    client = MongoClient(mongo_url, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
        database = client[database_name]
        existing_collections = set(database.list_collection_names())
        for collection_name, index_name in INDEXES:
            if collection_name not in existing_collections:
                database.create_collection(collection_name)
                existing_collections.add(collection_name)
                print(f"{database_name}.{collection_name}: created empty collection.")
            collection = database[collection_name]
            existing = {index.get("name") for index in collection.list_search_indexes()}
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
                "Wait for the Atlas index status to become READY before vector queries."
            )
    finally:
        client.close()


if __name__ == "__main__":
    main()
