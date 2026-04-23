from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.services.auth import auth_service
from src.schemas.users import UserResponse, UserShchema
from src.schemas.auth import TokenSchema
from src.repository import users as repository_users, auth as repository_auth

router = APIRouter(prefix="/auth", tags=["auth"])

get_refresh_token = HTTPBearer()


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="Successfully created",
)
async def register(body: UserShchema, db: AsyncSession = Depends(get_db)):
    """Register a new user account and return created user data."""
    user = await repository_users.get_user_by_email(email=body.email, db=db)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body=body, db=db)
    return new_user


@router.post("/signin", response_model=TokenSchema, response_description="Success")
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Authenticate user credentials and return access/refresh tokens."""
    user = await repository_users.get_user_by_email(email=body.username, db=db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    is_match_password = auth_service.verify_password(body.password, user.password)
    if not is_match_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    # Generate JWT
    access_token = auth_service.create_access_token(payload={"sub": user.email})
    refresh_token = auth_service.create_refresh_token(payload={"sub": user.email})

    await repository_auth.add_refresh_token(token=refresh_token, user_id=user.id, db=db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse, response_description="Success")
async def get_me(user: User = Depends(auth_service.get_current_user)) -> UserResponse:
    """Return current authenticated user profile."""
    return user


@router.get(
    "/refresh-token", response_model=TokenSchema, response_description="Success"
)
# Rotate refresh token and issue a new access/refresh pair.
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
    db: AsyncSession = Depends(get_db),
) -> TokenSchema:
    """Validate refresh token, rotate it, and return a fresh token pair."""
    # We intentionally return one generic 401 message for all auth failures
    # to avoid exposing which validation step failed.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Read raw refresh token from the Authorization: Bearer <token> header.
    token = credentials.credentials
    # Validate JWT signature/expiration, ensure refresh scope, and extract user email.
    email = auth_service.extract_email_from_refresh_jwt(token)

    # User might be deleted/disabled after token issuance; reject refresh in that case.
    user = await repository_users.get_user_by_email(email=email, db=db)
    if user is None:
        raise credentials_exception

    # Token must exist in the refresh_tokens table to be considered active.
    # This blocks replay of revoked/rotated tokens.
    db_token = await repository_auth.get_refresh_token_by_token(token=token, db=db)
    if db_token is None:
        # Security policy: if one invalid refresh token is presented for this user,
        # revoke all active refresh tokens for that user to force full re-login.
        await repository_auth.delete_refresh_tokens_by_user_id(user_id=user.id, db=db)
        raise credentials_exception

    # Issue a fresh access token and rotate refresh token to reduce replay window.
    access_token = auth_service.create_access_token(payload={"sub": email})
    new_refresh_token = auth_service.create_refresh_token(payload={"sub": email})
    updated = await repository_auth.update_refresh_token(
        old_token=token, new_token=new_refresh_token, db=db
    )
    if updated is None:
        raise credentials_exception

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Successfully logged out",
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Revoke refresh token so it cannot be used for further refresh requests."""
    token = credentials.credentials
    await repository_auth.delete_refresh_token_by_token(token=token, db=db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
