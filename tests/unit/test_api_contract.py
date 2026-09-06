import unittest

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.collection import CollectionCreate
from app.models.comment import CommentCreate, CommentUpdate
from app.models.user import PublicUserResponse


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_invalid_collection_ids_are_client_errors_without_database(self):
        for path in (
            "/collections/not-an-id",
            "/collections/not-an-id/movies",
            "/collections/user/not-an-id",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get("/api/v1" + path).status_code, 400)

    def test_refresh_requires_refresh_token_body(self):
        self.assertEqual(self.client.post("/api/v1/auth/refresh").status_code, 422)

    def test_invalid_authorization_does_not_silently_become_anonymous(self):
        self.assertEqual(
            self.client.get(
                "/api/v1/movies", headers={"Authorization": "Bearer invalid"}
            ).status_code,
            401,
        )

    def test_blank_and_oversized_inputs_rejected(self):
        for model, values in [
            (CollectionCreate, {"name": "  "}),
            (CommentCreate, {"text": "  "}),
            (CommentUpdate, {"text": None}),
            (CommentCreate, {"text": "x" * 2001}),
        ]:
            with self.subTest(model=model):
                with self.assertRaises(ValidationError):
                    model(**values)
        self.assertEqual(CollectionCreate(name="  Test  ").name, "Test")

    def test_public_user_schema_excludes_private_fields(self):
        fields = PublicUserResponse.model_fields
        self.assertNotIn("email", fields)
        self.assertNotIn("hashed_password", fields)
        self.assertNotIn("embedding", fields)
