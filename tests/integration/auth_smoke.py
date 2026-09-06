"""Exercise the complete auth-session contract against a running API and MongoDB."""

from __future__ import annotations

import concurrent.futures
import os
import uuid

import httpx
from pymongo import MongoClient

API_ORIGIN = os.getenv("TEST_BACKEND_ORIGIN", "http://127.0.0.1:8000")
AUTH_URL = f"{API_ORIGIN}/api/v1/auth"
MONGODB_URL = os.getenv(
    "MONGODB_URL", "mongodb://localhost:27018/?directConnection=true"
)
MONGODB_DB = os.getenv("MONGODB_DB", "cinemate")
PASSWORD = "StrongPass123!"
NEW_PASSWORD = "NewStrongPass456!"


def request(
    client: httpx.Client, method: str, path: str, **kwargs: object
) -> httpx.Response:
    return client.request(method, f"{AUTH_URL}{path}", **kwargs)


def expect(response: httpx.Response, status_code: int) -> None:
    if response.status_code != status_code:
        raise AssertionError(
            f"{response.request.method} {response.request.url.path}: "
            f"expected {status_code}, got {response.status_code}"
        )


def login(client: httpx.Client, email: str, password: str) -> dict[str, object]:
    response = request(
        client,
        "POST",
        "/login",
        json={"email": email, "password": password},
    )
    expect(response, 200)
    return response.json()


def main() -> None:
    email = f"ci-auth-{uuid.uuid4().hex}@example.com"
    with httpx.Client(timeout=15) as client:
        registered = request(
            client,
            "POST",
            "/register",
            json={"email": email, "name": "CI Auth", "password": PASSWORD},
        )
        expect(registered, 201)
        pair = registered.json()
        required_fields = {
            "user",
            "token_type",
            "access_token",
            "refresh_token",
            "access_expires_in",
            "refresh_expires_in",
        }
        if not required_fields.issubset(pair) or pair["token_type"] != "bearer":
            raise AssertionError("Register response does not match the token contract")

        access_token = pair["access_token"]
        refresh_token = pair["refresh_token"]
        expect(
            request(
                client,
                "GET",
                "/me",
                headers={"Authorization": f"Bearer {access_token}"},
            ),
            200,
        )
        expect(
            request(
                client,
                "GET",
                "/me",
                headers={"Authorization": f"Bearer {refresh_token}"},
            ),
            401,
        )

        rotated_response = request(
            client, "POST", "/refresh", json={"refresh_token": refresh_token}
        )
        expect(rotated_response, 200)
        rotated_token = rotated_response.json()["refresh_token"]
        expect(
            request(client, "POST", "/refresh", json={"refresh_token": refresh_token}),
            401,
        )
        expect(
            request(client, "POST", "/refresh", json={"refresh_token": rotated_token}),
            401,
        )
        expect(
            request(client, "POST", "/logout", json={"refresh_token": rotated_token}),
            204,
        )

        device_one = login(client, email, PASSWORD)
        device_two = login(client, email, PASSWORD)
        expect(
            request(
                client,
                "POST",
                "/logout",
                json={"refresh_token": device_one["refresh_token"]},
            ),
            204,
        )
        expect(
            request(
                client,
                "POST",
                "/refresh",
                json={"refresh_token": device_one["refresh_token"]},
            ),
            401,
        )
        device_two_rotated = request(
            client,
            "POST",
            "/refresh",
            json={"refresh_token": device_two["refresh_token"]},
        )
        expect(device_two_rotated, 200)
        expect(
            request(
                client,
                "POST",
                "/logout-all",
                headers={"Authorization": f"Bearer {device_two['access_token']}"},
            ),
            204,
        )
        expect(
            request(
                client,
                "POST",
                "/refresh",
                json={"refresh_token": device_two_rotated.json()["refresh_token"]},
            ),
            401,
        )

        password_pair = login(client, email, PASSWORD)
        expect(
            request(
                client,
                "POST",
                "/change-password",
                headers={"Authorization": f"Bearer {password_pair['access_token']}"},
                json={
                    "current_password": PASSWORD,
                    "new_password": NEW_PASSWORD,
                },
            ),
            204,
        )
        expect(
            request(
                client,
                "POST",
                "/refresh",
                json={"refresh_token": password_pair["refresh_token"]},
            ),
            401,
        )
        expect(
            request(
                client,
                "POST",
                "/login",
                json={"email": email, "password": PASSWORD},
            ),
            401,
        )
        login(client, email, NEW_PASSWORD)

        concurrent_pair = login(client, email, NEW_PASSWORD)
        concurrent_token = concurrent_pair["refresh_token"]

    def refresh_once(_: int) -> int:
        return httpx.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": concurrent_token},
            timeout=15,
        ).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        refresh_statuses = sorted(pool.map(refresh_once, range(2)))
    if refresh_statuses != [200, 401]:
        raise AssertionError(
            f"Concurrent refresh statuses were {refresh_statuses}, expected [200, 401]"
        )

    mongo = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=10_000)
    try:
        user_id = pair["user"]["_id"]
        sessions = list(mongo[MONGODB_DB].refresh_sessions.find({"user_id": user_id}))
        if not sessions:
            raise AssertionError("No refresh sessions were persisted")
        for session in sessions:
            if "refresh_token" in session or "token" in session:
                raise AssertionError("A plaintext refresh token was persisted")
            token_hash = session.get("token_hash", "")
            if len(token_hash) != 64 or "." in token_hash:
                raise AssertionError("A refresh session contains an invalid token hash")
    finally:
        mongo.close()

    print(
        "Auth integration passed: rotation/reuse, logout, two devices, "
        "logout-all, password change, concurrency, and hashed storage."
    )


if __name__ == "__main__":
    main()
