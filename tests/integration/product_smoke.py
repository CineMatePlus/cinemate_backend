"""Product contract checks using only uniquely named test-owned records.

Run against an isolated TEST_BACKEND_ORIGIN / MONGODB_DB. No database is dropped.
"""

import concurrent.futures
import os
import uuid

import httpx
from bson import ObjectId
from pymongo import MongoClient


def main():
    origin = os.environ.get("TEST_BACKEND_ORIGIN", "http://127.0.0.1:8012")
    db_name = os.environ.get("MONGODB_DB", "cinemate_acceptance")
    if not (db_name.endswith("_acceptance") or db_name.endswith("_ci")):
        raise SystemExit("Use an isolated *_acceptance or *_ci database.")
    mongo = MongoClient(
        os.environ.get(
            "MONGODB_URL", "mongodb://localhost:27018/?directConnection=true"
        )
    )
    db = mongo[db_name]
    user_ids = []
    movie_id = ObjectId()
    prefix = uuid.uuid4().hex
    db.movies.insert_one(
        {
            "_id": movie_id,
            "id": -int(prefix[:8], 16),
            "title": "Acceptance fixture",
            "overview": "A test movie",
            "poster_path": None,
            "backdrop_path": None,
            "vote_average": 7.0,
            "release_date": "2020-01-01",
            "genres": ["Drama"],
            "num_likes": 0,
            "num_watches": 0,
            "num_comments": 0,
        }
    )
    try:
        with httpx.Client(base_url=origin + "/api/v1", timeout=30) as client:

            def call(method, path, code=200, token=None, **kwargs):
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                response = client.request(method, path, headers=headers, **kwargs)
                assert response.status_code == code, (
                    method,
                    path,
                    response.status_code,
                    response.text[:200],
                )
                return response.json() if response.content else None

            pairs = []
            for i in range(2):
                pair = call(
                    "POST",
                    "/auth/register",
                    201,
                    json={
                        "email": f"{prefix}-{i}@example.com",
                        "name": f"Test {i}",
                        "password": "AcceptancePass123!",
                    },
                )
                pairs.append(pair)
                user_ids.append(ObjectId(pair["user"]["_id"]))
            a, b = [p["access_token"] for p in pairs]
            coll = call(
                "POST",
                "/collections",
                201,
                a,
                json={"name": "Private fixture", "is_public": False},
            )
            cid = coll["_id"]
            call("GET", f"/collections/{cid}", 403)
            call("GET", f"/collections/{cid}/movies", 403, b)
            call("PUT", f"/collections/{cid}", 403, b, json={"name": "Stolen"})
            call("DELETE", f"/collections/{cid}", 403, b)
            call("POST", f"/collections/{cid}/movies/{movie_id}", 204, a)
            call("POST", f"/collections/{cid}/movies/{movie_id}", 204, a)
            assert len(call("GET", f"/collections/{cid}/movies", token=a)) == 1
            call("PUT", f"/collections/{cid}", token=a, json={"is_public": True})
            assert call("GET", f"/collections/{cid}")["name"] == "Private fixture"
            call("GET", "/collections/not-an-id", 400)
            call("POST", "/collections", 422, a, json={"name": "  "})
            comment = call(
                "POST",
                f"/comments/{movie_id}",
                token=a,
                json={"text": "A useful review"},
            )
            assert "email" not in comment["user"]
            comment_id = comment["comment"]["_id"]
            call("PUT", f"/comments/{comment_id}", 403, b, json={"text": "Hijacked"})
            call("DELETE", f"/comments/{comment_id}", 403, b)
            call(
                "PUT",
                f"/comments/{comment_id}",
                token=a,
                json={"text": "Edited review"},
            )
            call("DELETE", f"/comments/{comment_id}", token=a)
            call("DELETE", f"/comments/{comment_id}", 404, a)
            assert db.movies.find_one({"_id": movie_id})["num_comments"] == 0

            def toggle(_):
                response = httpx.post(
                    origin + f"/api/v1/interactions/{movie_id}/like",
                    headers={"Authorization": f"Bearer {a}"},
                    timeout=30,
                )
                assert response.status_code == 200, response.text

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(toggle, range(8)))
            assert db.movies.find_one({"_id": movie_id})["num_likes"] == 0
            assert db.interactions.count_documents({"movie_id": movie_id}) == 0
            call("POST", f"/interactions/{movie_id}/watchlist", token=a)
            assert len(call("GET", "/users/me/watchlist", token=a)) == 1
            assert call("GET", "/users/me/watchlist", token=b) == []
            call("DELETE", f"/collections/{cid}", 204, a)
        print(
            "Product smoke passed: ownership, public privacy, validation, collections, comments, concurrent toggles, account isolation."
        )
    finally:
        db.collections.delete_many({"user_id": {"$in": user_ids}})
        db.comments.delete_many({"movie_id": str(movie_id)})
        db.interactions.delete_many({"movie_id": movie_id})
        db.refresh_sessions.delete_many(
            {"user_id": {"$in": [str(u) for u in user_ids] + user_ids}}
        )
        db.users.delete_many({"_id": {"$in": user_ids}})
        db.movies.delete_one({"_id": movie_id})
        mongo.close()


if __name__ == "__main__":
    main()
