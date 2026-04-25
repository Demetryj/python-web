from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.services.auth import auth_service
from src.services.email import send_email
from src.schemas.users import UserResponse, UserShchema
from src.schemas.auth import TokenSchema, RequestEmail
from src.repository import users as repository_users, auth as repository_auth
from src.config.rate_limiters import (
    auth_base_limiter,
    auth_request_email_limiter,
    auth_confirm_email_limiter,
    auth_refresh_token_limiter,
    auth_signup_limiter,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    # Base limit for all auth endpoints
    dependencies=[Depends(RateLimiter(limiter=auth_base_limiter))],
)

get_refresh_token = HTTPBearer()


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="Successfully created",
    # Stricter anti-bruteforce limit
    dependencies=[Depends(RateLimiter(limiter=auth_signup_limiter))],
)
async def register(
    body: UserShchema,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account and return created user data."""
    user = await repository_users.get_user_by_email(email=body.email, db=db)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body=body, db=db)

    background_tasks.add_task(
        send_email,
        email=new_user.email,
        username=new_user.username,
        host=request.base_url,
    )
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

    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
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


@router.get(
    "/refresh-token",
    response_model=TokenSchema,
    response_description="Success",
    dependencies=[Depends(RateLimiter(limiter=auth_refresh_token_limiter))],
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


@router.get(
    "/confirm-email/{token}",
    response_description="Successful email verification",
    dependencies=[Depends(RateLimiter(limiter=auth_confirm_email_limiter))],
)
async def confirm_email(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Confirm user's email by verification token and return status message."""
    email = await auth_service.get_email_from_email_token(token=token)
    user = await repository_users.get_user_by_email(email=email, db=db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )

    if user.confirmed:
        return {"message": "Your email is already confirmed"}

    await repository_users.confirm_email(email=email, db=db)
    return {"message": "Email confirmed"}


@router.post(
    "/request-email",
    response_description="Success",
    dependencies=[Depends(RateLimiter(limiter=auth_request_email_limiter))],
)
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await repository_users.get_user_by_email(email=body.email, db=db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, email=user.email, username=user.username, host=request.base_url
        )
    return {"message": "Check your email for confirmation."}
