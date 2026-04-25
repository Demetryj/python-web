from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db
from src.config.settings import settings
from src.entity.models import User
from src.repository import auth as repository_auth
from src.repository import users as repository_users


class AuthService:
    """Service layer for password hashing, JWT handling, and user auth context."""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = "HS256"
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")
    access_token_expire_minutes = 15
    refresh_token_expire_days = 7

    # Verify plain password against hashed value.
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Return True if plain password matches hashed password."""
        return self.pwd_context.verify(plain_password, hashed_password)

    # Hash plain user password.
    def get_password_hash(self, plain_password: str) -> str:
        """Return bcrypt hash for the provided plain password."""
        return self.pwd_context.hash(plain_password)

    # Create signed JWT token with scope and expiration claims.
    def create_token(
        self,
        payload: dict[str, Any],
        token_scope: str,
        expires_delta: timedelta,
    ) -> str:
        """Build and sign JWT token payload with common claims."""
        current_datetime = datetime.now(timezone.utc)
        expire_datetime = current_datetime + expires_delta

        payload = payload.copy()
        payload.update(
            {
                "iat": current_datetime,
                "exp": expire_datetime,
                "scope": token_scope,
            }
        )
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    # Create short-lived access token.
    def create_access_token(
        self, payload: dict[str, Any], expires_delta: Optional[float] = None
    ) -> str:
        """Return access token for user identity payload."""
        return self.create_token(
            payload=payload,
            token_scope="access_token",
            expires_delta=timedelta(
                minutes=(
                    expires_delta if expires_delta else self.access_token_expire_minutes
                )
            ),
        )

    # Create longer-lived refresh token.
    def create_refresh_token(
        self, payload: dict[str, Any], expires_delta: Optional[float] = None
    ) -> str:
        """Return refresh token for token renewal flow."""
        return self.create_token(
            payload=payload,
            token_scope="refresh_token",
            expires_delta=timedelta(
                days=expires_delta if expires_delta else self.refresh_token_expire_days
            ),
        )

    # Decode and validate JWT signature/expiration.
    def decode_token(self, token: str) -> dict[str, Any]:
        """Return decoded JWT payload."""
        return jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])

    # Extract email from refresh JWT without database checks.
    def extract_email_from_refresh_jwt(self, refresh_token: str) -> str:
        """Return email from refresh JWT payload or raise 401."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = self.decode_token(refresh_token)
            if payload.get("scope") != "refresh_token":
                raise credentials_exception
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
            return email
        except JWTError:
            raise credentials_exception

    # Extract email from refresh token and ensure token exists in DB.
    async def get_email_from_refresh_token(
        self, refresh_token: str, db: AsyncSession
    ) -> str:
        """Return email from valid refresh token or raise 401."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = self.decode_token(refresh_token)
            if payload.get("scope") != "refresh_token":
                raise credentials_exception

            db_token = await repository_auth.get_refresh_token_by_token(
                refresh_token, db
            )
            if db_token is None:
                raise credentials_exception

            email = payload.get("sub")
            if email is None:
                raise credentials_exception

            return email
        except JWTError:
            raise credentials_exception
            
    # Resolve current user from valid access token.
    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        """Return current authenticated user from access token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = self.decode_token(token)
            if payload.get('scope') == 'access_token':
                email = payload.get('sub')
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user


# Shared auth service instance.
auth_service = AuthService()
