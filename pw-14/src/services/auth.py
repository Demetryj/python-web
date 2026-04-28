import hashlib
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
    ALGORITHM = settings.hash_algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")
    access_token_expire_minutes = 15
    refresh_token_expire_days = 7
    password_reset_token_minutes = 15
    access_token_name = "access_token"
    refresh_token_name = "refresh_token"
    email_token_name = "email_token"
    password_reset_token = "password_reset_token"

    # Verify plain password against hashed value.
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Return True if plain password matches hashed password."""
        return self.pwd_context.verify(plain_password, hashed_password)

    # Hash plain user password.
    def get_password_hash(self, plain_password: str) -> str:
        """Return bcrypt hash for the provided plain password."""
        return self.pwd_context.hash(plain_password)
    
    # Build stable hash for storing and looking up password reset tokens.
    def get_token_hash(self, token: str) -> str:
        """Return deterministic SHA-256 hash for the provided password reset token."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

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
            token_scope=self.access_token_name,
            expires_delta=timedelta(
                minutes=(
                    expires_delta if expires_delta else self.access_token_expire_minutes
                )
            ),
        )

    # Create token for email confirmation flow.
    def create_email_token(
        self, payload: dict[str, Any], expires_delta: Optional[int] = None
    ) -> str:
        """Return JWT token with `email_token` scope for email confirmation."""
        return self.create_token(
            payload=payload,
            token_scope=self.email_token_name,
            expires_delta=timedelta(
                days=expires_delta if expires_delta else self.refresh_token_expire_days
            ),
        )
        
    # Create short-lived token for password reset flow.
    def create_password_reset_token(
        self, payload: dict[str, Any], expires_delta: Optional[int] = None
    ) -> str:
        """Return JWT token with `password_reset_token` scope for password reset."""
        return self.create_token(
            payload=payload,
            token_scope=self.password_reset_token,
            expires_delta=timedelta(
                minutes=expires_delta if expires_delta else self.password_reset_token_minutes
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
            if payload.get("scope") != self.refresh_token_name :
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
            if payload.get("scope") != self.refresh_token_name:
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
        
    # Validate email-confirmation token and extract user's email from `sub`.
    async def get_email_from_email_token(self, token: str) -> str:
        """Return email from valid email-confirmation token or raise 401."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token for email verification",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = self.decode_token(token)
            if payload.get("scope") != self.email_token_name:
                raise credentials_exception
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
            return email
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )
            
    # Validate password reset token and extract user's email from `sub`.
    async def get_email_from_password_reset_token(self, token: str) -> str:
        """Return email from valid password reset token or raise 400."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

        try:
            payload = self.decode_token(token)
            if payload.get("scope") != self.password_reset_token:
                raise credentials_exception

            email = payload.get("sub")
            if email is None:
                raise credentials_exception
            return email
        except JWTError:
            raise credentials_exception

    # Validate password reset token against JWT claims and stored DB state.
    async def validate_password_reset_token(
        self, token: str, db: AsyncSession
    ) -> str:
        """Return email from valid password reset token or raise 400."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

        # Validate JWT signature, expiration, and password-reset scope.
        email = await self.get_email_from_password_reset_token(token)

        # Look up the stored reset token row by deterministic token hash.
        token_hash = self.get_token_hash(token)
        db_token_obj = await repository_auth.get_password_reset_token(
            token_hash=token_hash,
            db=db,
        )

        # Reject tokens that were never issued by this application.
        if db_token_obj is None:
            raise credentials_exception

        # Reject replay attempts for already used password reset links.
        if db_token_obj.used_at is not None:
            raise credentials_exception

        # Reject tokens whose DB expiration timestamp has already passed.
        if db_token_obj.expires_at <= datetime.now():
            raise credentials_exception

        return email
             
    # Validate access token, authorize request, and resolve current user.
    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        """Authorize request by access token and return the current user."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = self.decode_token(token)
            if payload.get('scope') == self.access_token_name:
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
