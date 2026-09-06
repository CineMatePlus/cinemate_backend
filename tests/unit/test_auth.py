import asyncio
import copy
import unittest
from datetime import timedelta
from types import SimpleNamespace

import jwt
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import settings
from app.models.auth import ChangePasswordRequest, RegisterRequest
from app.services.auth import AuthService


def matches(document, query):
    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict):
            if "$gt" in expected and not (actual > expected["$gt"]):
                return False
            if "$ne" in expected and actual == expected["$ne"]:
                return False
            continue
        if actual != expected:
            return False
    return True


def apply_update(document, update):
    for key, value in update.get("$set", {}).items():
        document[key] = value


class FakeCollection:
    def __init__(self):
        self.documents = []
        self.next_id = 1

    async def insert_one(self, document, session=None):
        stored = copy.deepcopy(document)
        stored.setdefault("_id", f"fake-{self.next_id}")
        self.next_id += 1
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    async def find_one(self, query, session=None):
        return next(
            (copy.deepcopy(item) for item in self.documents if matches(item, query)),
            None,
        )

    async def find_one_and_update(
        self, query, update, return_document=None, session=None
    ):
        for item in self.documents:
            if matches(item, query):
                apply_update(item, update)
                return copy.deepcopy(item)
        return None

    async def update_one(self, query, update, session=None):
        for item in self.documents:
            if matches(item, query):
                apply_update(item, update)
                return SimpleNamespace(modified_count=1)
        return SimpleNamespace(modified_count=0)

    async def update_many(self, query, update, session=None):
        modified = 0
        for item in self.documents:
            if matches(item, query):
                apply_update(item, update)
                modified += 1
        return SimpleNamespace(modified_count=modified)


class FakeDatabase:
    def __init__(self):
        self.users = FakeCollection()
        self.refresh_sessions = FakeCollection()


class PasswordPolicyTests(unittest.TestCase):
    def test_accepts_configured_boundaries(self):
        minimum = "a" * settings.PASSWORD_MIN_LENGTH
        maximum = "a" * settings.PASSWORD_MAX_LENGTH
        self.assertEqual(
            RegisterRequest(
                email="test@example.com", name="Test", password=minimum
            ).password,
            minimum,
        )
        self.assertEqual(
            ChangePasswordRequest(
                current_password="old", new_password=maximum
            ).new_password,
            maximum,
        )

    def test_rejects_length_blank_unicode_bytes_and_invalid_email(self):
        invalid_passwords = [
            "a" * (settings.PASSWORD_MIN_LENGTH - 1),
            "a" * (settings.PASSWORD_MAX_LENGTH + 1),
            " " * settings.PASSWORD_MIN_LENGTH,
            "😀" * 19,
        ]
        for password in invalid_passwords:
            with self.subTest(password=password), self.assertRaises(ValidationError):
                RegisterRequest(
                    email="test@example.com", name="Test", password=password
                )
        with self.assertRaises(ValidationError):
            RegisterRequest(email="not-an-email", name="Test", password="password")


class AuthTokenTests(unittest.TestCase):
    def setUp(self):
        self.service = AuthService(FakeDatabase())

    def test_required_claims_and_token_type_are_enforced(self):
        access, access_claims = self.service._create_token(
            subject="test@example.com",
            token_type="access",
            expires_delta=timedelta(minutes=5),
        )
        decoded = self.service.decode_token(access, "access")
        self.assertTrue({"sub", "type", "jti", "iat", "exp"} <= decoded.keys())
        self.assertNotIn("family_id", access_claims)
        with self.assertRaises(HTTPException):
            self.service.decode_token(access, "refresh")

    def test_expired_malformed_and_wrong_signature_tokens_are_rejected(self):
        expired, _ = self.service._create_token(
            subject="test@example.com",
            token_type="access",
            expires_delta=timedelta(seconds=-1),
        )
        wrong_signature = jwt.encode(
            {
                "sub": "test@example.com",
                "type": "access",
                "jti": "wrong-signature",
                "iat": 1,
                "exp": 4_102_444_800,
            },
            "different-secret",
            algorithm=settings.JWT_ALGORITHM,
        )
        for token in (expired, "not-a-jwt", wrong_signature):
            with self.subTest(token=token), self.assertRaises(HTTPException):
                self.service.decode_token(token, "access")


class RefreshSessionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.database = FakeDatabase()
        self.service = AuthService(self.database)
        self.auth = await self.service.register_user(
            {
                "email": "person@example.com",
                "name": "Person",
                "password": "password",
            }
        )

    async def test_plaintext_refresh_token_is_never_persisted(self):
        session = self.database.refresh_sessions.documents[0]
        self.assertNotIn(self.auth.refresh_token, session.values())
        self.assertEqual(len(session["token_hash"]), 64)

    async def test_rotation_reuse_revokes_the_whole_family(self):
        rotated = await self.service.refresh_token(self.auth.refresh_token)
        with self.assertRaises(HTTPException):
            await self.service.refresh_token(self.auth.refresh_token)
        family_id = self.service.decode_token(rotated.refresh_token, "refresh")[
            "family_id"
        ]
        family = [
            item
            for item in self.database.refresh_sessions.documents
            if item["family_id"] == family_id
        ]
        self.assertTrue(family)
        self.assertTrue(all(item["revoked_at"] is not None for item in family))
        with self.assertRaises(HTTPException):
            await self.service.refresh_token(rotated.refresh_token)

    async def test_two_concurrent_refreshes_allow_only_one(self):
        results = await asyncio.gather(
            self.service.refresh_token(self.auth.refresh_token),
            self.service.refresh_token(self.auth.refresh_token),
            return_exceptions=True,
        )
        self.assertEqual(sum(not isinstance(item, Exception) for item in results), 1)

    async def test_logout_all_and_password_change_revoke_sessions(self):
        second = await self.service.login_user("person@example.com", "password")
        user = await self.service.get_current_user(self.auth.access_token)
        await self.service.logout_all(user)
        self.assertTrue(
            all(
                item["revoked_at"] is not None
                for item in self.database.refresh_sessions.documents
            )
        )
        with self.assertRaises(HTTPException):
            await self.service.refresh_token(second.refresh_token)

        third = await self.service.login_user("person@example.com", "password")
        await self.service.change_password(user, "password", "new-password")
        with self.assertRaises(HTTPException):
            await self.service.refresh_token(third.refresh_token)
        self.assertIsNotNone(
            await self.service.authenticate_user("person@example.com", "new-password")
        )


if __name__ == "__main__":
    unittest.main()
