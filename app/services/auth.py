import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

import bcrypt
import jwt
from fastapi import HTTPException, status
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.db.mongodb import get_database
from app.models.auth import AuthResponse
from app.models.user import UserInDB, UserResponse

TokenType = Literal["access", "refresh"]


class RefreshSessionRejected(Exception):
    def __init__(self, known_token: bool):
        self.known_token = known_token


class AuthService:
    def __init__(self, database: Any = None):
        self.db = database if database is not None else get_database()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _credentials_exception() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _user_response(user: UserInDB) -> UserResponse:
        return UserResponse(
            _id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            gender=user.gender,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def get_user(self, username: str) -> Optional[UserInDB]:
        user = await self.db.users.find_one({"email": username})
        if not user:
            return None
        now = datetime.now(timezone.utc)
        return UserInDB(
            _id=str(user["_id"]),
            email=user["email"],
            name=user.get("name", ""),
            avatar_url=user.get("avatar_url"),
            gender=user.get("gender", 2),
            hashed_password=user["hashed_password"],
            created_at=user.get("created_at", now),
            updated_at=user.get("updated_at", now),
        )

    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[UserInDB]:
        user = await self.get_user(username)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user

    def _create_token(
        self,
        *,
        subject: str,
        token_type: TokenType,
        expires_delta: timedelta,
        family_id: Optional[str] = None,
    ) -> tuple[str, dict[str, Any]]:
        now = datetime.now(timezone.utc)
        claims: dict[str, Any] = {
            "sub": subject,
            "type": token_type,
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + expires_delta,
        }
        if token_type == "refresh":
            if not family_id:
                raise ValueError("Refresh tokens require a family_id")
            claims["family_id"] = family_id
        token = jwt.encode(
            claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return token, claims

    def decode_token(self, token: str, expected_type: TokenType) -> dict[str, Any]:
        try:
            claims = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"require": ["sub", "type", "jti", "iat", "exp"]},
            )
            if claims.get("type") != expected_type:
                raise self._credentials_exception()
            if expected_type == "refresh" and not claims.get("family_id"):
                raise self._credentials_exception()
            return claims
        except HTTPException:
            raise
        except jwt.PyJWTError as exc:
            raise self._credentials_exception() from exc

    async def _store_refresh_session(
        self,
        *,
        token: str,
        claims: dict[str, Any],
        user_id: str,
        session: Any = None,
    ) -> None:
        expires_at = claims["exp"]
        if not isinstance(expires_at, datetime):
            expires_at = datetime.fromtimestamp(expires_at, timezone.utc)
        await self.db.refresh_sessions.insert_one(
            {
                "token_hash": self._token_hash(token),
                "user_id": user_id,
                "jti": claims["jti"],
                "family_id": claims["family_id"],
                "expires_at": expires_at,
                "used_at": None,
                "revoked_at": None,
                "replaced_by": None,
                "created_at": datetime.now(timezone.utc),
            },
            session=session,
        )

    async def _issue_token_pair(
        self,
        user: UserInDB,
        family_id: Optional[str] = None,
        session: Any = None,
    ) -> AuthResponse:
        family_id = family_id or str(uuid4())
        access_token, _ = self._create_token(
            subject=user.email,
            token_type="access",
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token, refresh_claims = self._create_token(
            subject=user.email,
            token_type="refresh",
            family_id=family_id,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self._store_refresh_session(
            token=refresh_token,
            claims=refresh_claims,
            user_id=user.id,
            session=session,
        )
        return AuthResponse(
            user=self._user_response(user),
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    async def get_current_user(self, token: str) -> UserInDB:
        claims = self.decode_token(token, "access")
        user = await self.get_user(str(claims["sub"]))
        if user is None:
            raise self._credentials_exception()
        return user

    async def get_user_from_token(self, authorization: str) -> UserResponse:
        token = self.bearer_token(authorization)
        return self._user_response(await self.get_current_user(token))

    @staticmethod
    def bearer_token(authorization: str) -> str:
        scheme, separator, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not separator or not token.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token.strip()

    async def register_user(self, user_data: dict[str, Any]) -> AuthResponse:
        email = str(user_data["email"])
        if await self.get_user(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        now = datetime.now(timezone.utc)
        user_dict = {
            "email": email,
            "name": user_data["name"],
            "avatar_url": user_data.get("avatar_url"),
            "gender": int(user_data.get("gender", 2)),
            "hashed_password": self.get_password_hash(user_data["password"]),
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = await self.db.users.insert_one(user_dict)
        except DuplicateKeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            ) from exc
        user_dict["_id"] = str(result.inserted_id)
        user = UserInDB.model_validate(user_dict)
        return await self._issue_token_pair(user)

    async def login_user(self, username: str, password: str) -> AuthResponse:
        user = await self.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await self._issue_token_pair(user)

    async def _revoke_family(self, family_id: str, revoked_at: datetime) -> None:
        await self.db.refresh_sessions.update_many(
            {"family_id": family_id, "revoked_at": None},
            {"$set": {"revoked_at": revoked_at}},
        )

    async def refresh_token(self, token: str) -> AuthResponse:
        claims = self.decode_token(token, "refresh")
        now = datetime.now(timezone.utc)
        selector = {
            "jti": claims["jti"],
            "token_hash": self._token_hash(token),
            "family_id": claims["family_id"],
            "used_at": None,
            "revoked_at": None,
            "expires_at": {"$gt": now},
        }
        user = await self.get_user(str(claims["sub"]))
        if not user:
            raise self._credentials_exception()

        async def rotate(session: Any = None) -> AuthResponse:
            claimed = await self.db.refresh_sessions.find_one_and_update(
                selector,
                {"$set": {"used_at": now}},
                return_document=ReturnDocument.AFTER,
                session=session,
            )
            if not claimed:
                known = await self.db.refresh_sessions.find_one(
                    {"jti": claims["jti"], "family_id": claims["family_id"]},
                    session=session,
                )
                raise RefreshSessionRejected(known_token=bool(known))
            if claimed.get("user_id") != user.id:
                raise RefreshSessionRejected(known_token=True)

            response = await self._issue_token_pair(
                user, claims["family_id"], session=session
            )
            replacement = self.decode_token(response.refresh_token, "refresh")
            await self.db.refresh_sessions.update_one(
                {"jti": claims["jti"]},
                {"$set": {"replaced_by": replacement["jti"]}},
                session=session,
            )
            return response

        try:
            client = getattr(self.db, "client", None)
            if client is None:
                return await rotate()
            async with client.start_session() as session:
                return await session.with_transaction(rotate)
        except RefreshSessionRejected as exc:
            if exc.known_token:
                await self._revoke_family(claims["family_id"], now)
            raise self._credentials_exception() from exc
        except DuplicateKeyError as exc:
            await self._revoke_family(claims["family_id"], now)
            raise self._credentials_exception() from exc

    async def logout(self, token: str) -> None:
        claims = self.decode_token(token, "refresh")
        await self._revoke_family(claims["family_id"], datetime.now(timezone.utc))

    async def logout_all(self, user: UserInDB) -> None:
        now = datetime.now(timezone.utc)
        await self.db.refresh_sessions.update_many(
            {"user_id": user.id, "revoked_at": None},
            {"$set": {"revoked_at": now}},
        )

    async def change_password(
        self, user: UserInDB, current_password: str, new_password: str
    ) -> None:
        if not self.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        if self.verify_password(new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from the current password",
            )
        now = datetime.now(timezone.utc)
        await self.db.users.update_one(
            {"_id": self._database_id(user.id)},
            {
                "$set": {
                    "hashed_password": self.get_password_hash(new_password),
                    "updated_at": now,
                }
            },
        )
        await self.logout_all(user)

    @staticmethod
    def _database_id(user_id: str) -> Any:
        try:
            from bson import ObjectId

            return ObjectId(user_id)
        except Exception:
            return user_id
