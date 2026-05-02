"""Authentication and account recovery routes."""

from datetime import datetime, timedelta

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
from src.schemas.auth import TokenSchema, RequestEmail, ResetPasswordSchema
from src.repository import users as repository_users, auth as repository_auth
from src.config.messages import CHECK_EMAIL_FOR_CONFIRMATION, EMAIL_ALREADY_CONFIRMED, EMAIL_CONFIRMED, INVALID_OR_EXPIRED_PASSWORD_RESET_TOKEN, RESET_PASSWORD_EMAIL_EXITS, SUCCESS_TO_CREATE_NEW_PASSWORD, HTTPExceptionMessages
from src.config.rate_limiters import (
    auth_base_limiter,
    auth_request_email_limiter,
    auth_confirm_email_limiter,
    auth_refresh_token_limiter,
    auth_signup_limiter,
    auth_reset_password_limiter,
)

EMAIL_VERIFY_TITLE = "Confirm your email"
EMAIL_VERIFY_TEMPLATE = "verify_email.html"
RESET_PASSWORD_TITLE = "Reset your password"
RESET_PASSWORD_TEMPLATE = "reset_password.html"

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
    """Register a new user account.

    :param body: User registration payload.
    :type body: UserShchema
    :param background_tasks: FastAPI background task manager.
    :type background_tasks: BackgroundTasks
    :param request: Incoming request used to build email links.
    :type request: Request
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: Raises ``409 Conflict`` when the account exists.
    :return: Created user data.
    :rtype: UserResponse
    """
    user = await repository_users.get_user_by_email(email=body.email, db=db)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=HTTPExceptionMessages.account_already_exists.value,
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body=body, db=db)

    verification_token = auth_service.create_email_token({"sub": new_user.email})

    background_tasks.add_task(
        send_email,
        email=new_user.email,
        username=new_user.username,
        host=request.base_url,
        token=verification_token,
        subject=EMAIL_VERIFY_TITLE,
        template_name=EMAIL_VERIFY_TEMPLATE,
    )
    return new_user


@router.post("/signin", response_model=TokenSchema, response_description="Success")
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Authenticate a user and return access and refresh tokens.

    :param body: OAuth2 password form with username and password.
    :type body: OAuth2PasswordRequestForm
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: Raises ``401 Unauthorized`` for invalid credentials
        or an unconfirmed email.
    :return: Token response payload.
    :rtype: dict[str, str]
    """
    user = await repository_users.get_user_by_email(email=body.username, db=db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=HTTPExceptionMessages.invalid_email_or_password.value,
        )

    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=HTTPExceptionMessages.email_not_confirmed.value,
        )

    is_match_password = auth_service.verify_password(body.password, user.password)
    if not is_match_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=HTTPExceptionMessages.invalid_email_or_password.value,
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
    """Validate and rotate a refresh token.

    :param credentials: HTTP bearer credentials containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: Raises ``401 Unauthorized`` when the token cannot be
        validated.
    :return: Fresh access and refresh token pair.
    :rtype: TokenSchema
    """
    # We intentionally return one generic 401 message for all auth failures
    # to avoid exposing which validation step failed.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=HTTPExceptionMessages.could_not_validate_token.value,
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
    """Revoke a refresh token.

    :param credentials: HTTP bearer credentials containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Empty ``204 No Content`` response.
    :rtype: Response
    """
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
    """Confirm a user email address.

    :param token: Email confirmation token.
    :type token: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: Raises ``400 Bad Request`` when verification fails.
    :return: Confirmation status message.
    :rtype: dict[str, str]
    """
    email = auth_service.get_email_from_email_token(token=token)
    user = await repository_users.get_user_by_email(email=email, db=db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=HTTPExceptionMessages.verification_error.value
        )

    if user.confirmed:
        return {"message": EMAIL_ALREADY_CONFIRMED}

    await repository_users.confirm_email(email=email, db=db)
    return {"message": EMAIL_CONFIRMED}


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
) -> dict[str, str]:
    """Send a new email confirmation link.

    :param body: Request payload containing the target email address.
    :type body: RequestEmail
    :param background_tasks: FastAPI background task manager.
    :type background_tasks: BackgroundTasks
    :param request: Incoming request used to build email links.
    :type request: Request
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Request status message.
    :rtype: dict[str, str]
    """
    user = await repository_users.get_user_by_email(email=body.email, db=db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=HTTPExceptionMessages.not_found.value,
        )
    
    if user.confirmed:
        return {"message": EMAIL_ALREADY_CONFIRMED}
    if user:
        verification_token = auth_service.create_email_token({"sub": user.email})

        background_tasks.add_task(
            send_email,
            email=user.email,
            username=user.username,
            host=request.base_url,
            token=verification_token,
            subject=EMAIL_VERIFY_TITLE,
            template_name=EMAIL_VERIFY_TEMPLATE,
        )
    return {"message": CHECK_EMAIL_FOR_CONFIRMATION}


@router.post(
    "/password-reset/request",
    description="The route for sending the email address to which the email to confirm the password reset will be sent",
    dependencies=[Depends(RateLimiter(limiter=auth_reset_password_limiter))],
)
async def password_reset_request(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Request a password reset email.

    :param body: Request payload containing the target email address.
    :type body: RequestEmail
    :param background_tasks: FastAPI background task manager.
    :type background_tasks: BackgroundTasks
    :param request: Incoming request used to build reset links.
    :type request: Request
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Generic password reset request status message.
    :rtype: dict[str, str]
    """
    # Look up the account by email, but keep the response generic either way.
    user = await repository_users.get_user_by_email(email=body.email, db=db)
    if user:
        # Create a short-lived JWT reset token and persist its stable hash.
        token = auth_service.create_password_reset_token({"sub": user.email})
        token_hash = auth_service.get_token_hash(token)

        # Copy scalar user fields before commit expires ORM attributes in async session.
        user_email = user.email
        username = user.username
        user_id = user.id

        await repository_auth.add_password_reset_token(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now()
            + timedelta(minutes=auth_service.password_reset_token_minutes),
            db=db,
        )

        # Send reset instructions in the background so the API responds quickly.
        background_tasks.add_task(
            send_email,
            email=user_email,
            username=username,
            host=request.base_url,
            token=token,
            subject=RESET_PASSWORD_TITLE,
            template_name=RESET_PASSWORD_TEMPLATE,
        )
    return {"message": RESET_PASSWORD_EMAIL_EXITS}


@router.get(
    "/password-reset/verify/{token}",
    response_description="Success",
    dependencies=[Depends(RateLimiter(limiter=auth_reset_password_limiter))],
    # status_code=status.HTTP_204_NO_CONTENT,
)
async def reset_password(token: str, db: AsyncSession = Depends(get_db)) -> None:
    """Validate a password reset token.

    :param token: Password reset token.
    :type token: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: Raises ``400 Bad Request`` when the token is invalid
        or expired.
    :return: Password reset validation status message.
    :rtype: dict[str, str]
    """
    await auth_service.validate_password_reset_token(token=token, db=db)
    # return Response(status_code=status.HTTP_204_NO_CONTENT)
    return {
        "message": SUCCESS_TO_CREATE_NEW_PASSWORD,
    }


@router.patch(
    "/password-reset/confirm",
    dependencies=[Depends(RateLimiter(limiter=auth_reset_password_limiter))],
)
async def password_reset_confirm(
    body: ResetPasswordSchema, db: AsyncSession = Depends(get_db)
) -> None:
    """Set a new password after reset token validation.

    :param body: Password reset confirmation payload.
    :type body: ResetPasswordSchema
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: Raises ``400 Bad Request`` when the reset token is
        invalid, expired, or the user cannot be updated.
    :return: Empty ``204 No Content`` response.
    :rtype: Response
    """
    email = await auth_service.validate_password_reset_token(token=body.token, db=db)

    updated_user = await repository_users.update_user_password(
        email=email,
        hashed_password=auth_service.get_password_hash(body.password),
        db=db,
    )
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_OR_EXPIRED_PASSWORD_RESET_TOKEN,
        )

    token_hash = auth_service.get_token_hash(body.token)
    await repository_auth.update_used_status_password_reset_token(token_hash, db=db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
