"""Run one real Atlas Vector Search query against a disposable document."""

from __future__ import annotations

import os
import time

from pymongo import MongoClient

DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
INDEX_NAME = os.getenv("MOVIE_VECTOR_INDEX", "movie_vector_index")
SMOKE_ID = -9_999_999
WAIT_TIMEOUT_SECONDS = float(os.getenv("VECTOR_SMOKE_TIMEOUT_SECONDS", "60"))
POLL_INTERVAL_SECONDS = 1.0


def main() -> None:
    client = MongoClient(
        os.getenv("MONGODB_URL", "mongodb://localhost:27018/?directConnection=true"),
        serverSelectionTimeoutMS=10_000,
    )
    movies = client[os.getenv("MONGODB_DB", "cinemate")].movies
    vector = [1.0] + [0.0] * (DIMENSIONS - 1)
    try:
        movies.update_one(
            {"id": SMOKE_ID},
            {
                "$set": {
                    "id": SMOKE_ID,
                    "title": "Vector smoke test",
                    "overview": "Disposable CI document",
                    "embedding": vector,
                }
            },
            upsert=True,
        )
        deadline = time.monotonic() + WAIT_TIMEOUT_SECONDS
        while True:
            results = list(
                movies.aggregate(
                    [
                        {
                            "$vectorSearch": {
                                "index": INDEX_NAME,
                                "path": "embedding",
                                "queryVector": vector,
                                "numCandidates": 100,
                                "limit": 10,
                            }
                        }
                    ]
                )
            )
            if any(result.get("id") == SMOKE_ID for result in results):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "Vector Search did not index and return the smoke document "
                    f"within {WAIT_TIMEOUT_SECONDS:g} seconds"
                )
            time.sleep(POLL_INTERVAL_SECONDS)
        print(f"Vector Search smoke query passed with index {INDEX_NAME!r}.")
    finally:
        movies.delete_one({"id": SMOKE_ID})
        client.close()


if __name__ == "__main__":
    main()
