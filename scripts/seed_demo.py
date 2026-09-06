"""Create repeatable synthetic demo data in the explicitly selected demo database.

First seed movies normally with MONGODB_DB=cinemate_demo. Password is supplied
through DEMO_PASSWORD, never written to the repository or printed by this script.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bson import ObjectId
from pymongo import MongoClient

from app.core.config import settings
from app.models.auth import validate_password_policy
from app.services.auth import AuthService
from app.services.vector_math import average_vectors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, choices=["cinemate_demo"])
    args = parser.parse_args()
    password = os.environ.get("DEMO_PASSWORD", "")
    validate_password_policy(password)
    client = MongoClient(settings.MONGODB_URL)
    db = client[args.database]
    movies = list(
        db.movies.find({"embedding": {"$exists": True}}).sort("id", 1).limit(20)
    )
    if len(movies) < 12:
        raise SystemExit("Seed movies with embeddings first in cinemate_demo.")
    now = datetime.now(timezone.utc)
    for index, name in enumerate(["Deniz", "Ece", "Can"]):
        uid = ObjectId(f"c1de{index:020x}")
        email = f"demo{index + 1}@example.com"
        liked = movies[index : index + 8]
        db.users.update_one(
            {"_id": uid},
            {
                "$set": {
                    "name": name,
                    "email": email,
                    "gender": 2,
                    "avatar_url": None,
                    "hashed_password": AuthService.get_password_hash(password),
                    "embedding": average_vectors([m["embedding"] for m in liked]),
                    "embedding_model": settings.EMBEDDING_MODEL,
                    "embedding_dimensions": settings.EMBEDDING_DIMENSIONS,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        db.refresh_sessions.delete_many({"user_id": {"$in": [uid, str(uid)]}})
        db.interactions.delete_many({"user_id": uid})
        db.interactions.insert_many(
            [
                {
                    "user_id": uid,
                    "movie_id": movie["_id"],
                    "interaction_type": kind,
                    "created_at": now,
                }
                for kind, selected in [
                    ("like", liked),
                    ("watched", movies[index : index + 4]),
                    ("watchlist", movies[10:14]),
                ]
                for movie in selected
            ]
        )
        db.collections.update_one(
            {"user_id": uid, "name": "Hafta sonu listem"},
            {
                "$set": {
                    "description": "Demo için seçilmiş filmler",
                    "is_public": True,
                    "movie_ids": [m["_id"] for m in liked[:5]],
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        db.comments.update_one(
            {"user_id": str(uid), "demo_fixture": True},
            {
                "$set": {
                    "movie_id": str(movies[0]["_id"]),
                    "text": "Hikâyesi ve atmosferiyle tekrar izlemek istediğim bir film.",
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
    # Reconcile demo counters from source records; reruns cannot inflate them.
    for movie in db.movies.find({}, {"_id": 1}):
        mid = movie["_id"]
        db.movies.update_one(
            {"_id": mid},
            {
                "$set": {
                    "num_likes": db.interactions.count_documents(
                        {"movie_id": mid, "interaction_type": "like"}
                    ),
                    "num_watches": db.interactions.count_documents(
                        {"movie_id": mid, "interaction_type": "watched"}
                    ),
                    "num_comments": db.comments.count_documents({"movie_id": str(mid)}),
                }
            },
        )
    print(
        "Demo ready: 3 synthetic users, repeatable interactions, collections and comments. Password supplied through DEMO_PASSWORD."
    )
    client.close()


if __name__ == "__main__":
    main()
