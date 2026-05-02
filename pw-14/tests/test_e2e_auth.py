from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from src.config.messages import (
    CHECK_EMAIL_FOR_CONFIRMATION,
    EMAIL_ALREADY_CONFIRMED,
    EMAIL_CONFIRMED,
    INVALID_OR_EXPIRED_PASSWORD_RESET_TOKEN,
    HTTPExceptionMessages,
    RESET_PASSWORD_EMAIL_EXITS,
    SUCCESS_TO_CREATE_NEW_PASSWORD,
)
from src.entity.models import PasswordResetToken, RefreshToken, User
from src.services.auth import auth_service
from tests.conftest import TestingSessionLocal

PREFIX = "/api/auth"


@pytest.fixture()
def user_payload() -> dict[str, str]:
    """Return unique signup data so auth tests do not share state."""

    suffix = uuid4().hex
    return {
        "username": f"User {suffix[:8]}",
        "email": f"user.{suffix}@mail.com",
        "password": "1234567890",
    }


@pytest_asyncio.fixture()
async def registered_user(user_payload) -> User:
    """Create and return an unconfirmed user stored in the test database."""

    async with TestingSessionLocal() as session:
        user = User(
            username=user_payload["username"],
            email=user_payload["email"],
            password=auth_service.get_password_hash(user_payload["password"]),
            confirmed=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture()
async def confirmed_user(registered_user) -> User:
    """Mark the per-test registered user as confirmed and return it."""

    async with TestingSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == registered_user.id)
        )
        user = result.scalar_one()
        user.confirmed = True
        await session.commit()
        await session.refresh(user)
        return user


def test_signup(client, user_payload, monkeypatch) -> None:
    """Test that a new user can sign up successfully."""

    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    response = client.post(f"{PREFIX}/signup", json=user_payload)

    assert response.status_code == 201, response.text

    data = response.json()
    assert data["username"] == user_payload["username"]
    assert data["email"] == user_payload["email"]
    assert "password" not in data
    assert "avatar" in data

    mock_send_email.assert_called_once()


def test_signiup_if_user_already_exists(client, user_payload, monkeypatch) -> None:
    """Test that signup returns 409 when a user with the same email exists."""

    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    first_response = client.post(f"{PREFIX}/signup", json=user_payload)
    response = client.post(f"{PREFIX}/signup", json=user_payload)

    assert first_response.status_code == 201, first_response.text
    assert response.status_code == 409, response.text

    data = response.json()
    assert data["detail"] == HTTPExceptionMessages.account_already_exists.value


def test_signin_not_confirmed(client, registered_user, user_payload) -> None:
    """Test that an unconfirmed user cannot sign in and gets a 401 error."""

    response = client.post(
        f"{PREFIX}/signin",
        data={
            "username": registered_user.email,
            "password": user_payload["password"],
        },
    )

    assert response.status_code == 401, response.text
    assert response.json()["detail"] == HTTPExceptionMessages.email_not_confirmed.value


def test_signin(client, confirmed_user, user_payload) -> None:
    """Test that a confirmed registered user can sign in and receive tokens."""

    response = client.post(
        f"{PREFIX}/signin",
        data={
            "username": confirmed_user.email,
            "password": user_payload["password"],
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_signin_wrong_email(client, confirmed_user, user_payload) -> None:
    """Test that signin fails with 401 for an email that does not exist."""

    response = client.post(
        f"{PREFIX}/signin",
        data={
            "username": f"wrong.{uuid4().hex}@example.com",
            "password": user_payload["password"],
        },
    )

    assert response.status_code == 401, response.text
    assert (
        response.json()["detail"]
        == HTTPExceptionMessages.invalid_email_or_password.value
    )


def test_signin_wrong_password(client, confirmed_user) -> None:
    """Test that signin fails with 401 when the password is incorrect."""

    response = client.post(
        f"{PREFIX}/signin",
        data={
            "username": confirmed_user.email,
            "password": "wrong123",
        },
    )

    assert response.status_code == 401, response.text
    assert (
        response.json()["detail"]
        == HTTPExceptionMessages.invalid_email_or_password.value
    )


@pytest.mark.asyncio
async def test_log_out(client, confirmed_user, user_payload) -> None:
    """Test that logout revokes the issued refresh token and returns 204."""

    signin_response = client.post(
        f"{PREFIX}/signin",
        data={
            "username": confirmed_user.email,
            "password": user_payload["password"],
        },
    )

    assert signin_response.status_code == 200, signin_response.text
    refresh_token = signin_response.json()["refresh_token"]

    logout_response = client.post(
        f"{PREFIX}/logout",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert logout_response.status_code == 204, logout_response.text
    assert logout_response.text == ""

    async with TestingSessionLocal() as session:
        token_result = await session.execute(
            select(RefreshToken).where(RefreshToken.rf_token == refresh_token)
        )
        db_token = token_result.scalar_one_or_none()
        assert db_token is None


def test_log_out_revoked_token_cannot_be_refreshed(
    client, confirmed_user, user_payload
) -> None:
    """Test that a logged out refresh token cannot be used to refresh tokens again."""

    signin_response = client.post(
        f"{PREFIX}/signin",
        data={
            "username": confirmed_user.email,
            "password": user_payload["password"],
        },
    )

    assert signin_response.status_code == 200, signin_response.text
    refresh_token = signin_response.json()["refresh_token"]

    logout_response = client.post(
        f"{PREFIX}/logout",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert logout_response.status_code == 204, logout_response.text

    refresh_response = client.get(
        f"{PREFIX}/refresh-token",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert refresh_response.status_code == 401, refresh_response.text
    assert refresh_response.json()["detail"] == "Could not validate token"


# =========================================================================
# Refresh token
# =========================================================================
@pytest.mark.asyncio
async def test_refresh_token(client, confirmed_user, user_payload) -> None:
    """Test that refresh-token rotates the stored refresh token and returns a new pair."""

    signin_response = client.post(
        f"{PREFIX}/signin",
        data={
            "username": confirmed_user.email,
            "password": user_payload["password"],
        },
    )

    assert signin_response.status_code == 200, signin_response.text
    old_refresh_token = signin_response.json()["refresh_token"]

    refresh_response = client.get(
        f"{PREFIX}/refresh-token",
        headers={"Authorization": f"Bearer {old_refresh_token}"},
    )

    assert refresh_response.status_code == 200, refresh_response.text

    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    async with TestingSessionLocal() as session:
        new_token_result = await session.execute(
            select(RefreshToken).where(RefreshToken.rf_token == data["refresh_token"])
        )
        new_db_token = new_token_result.scalar_one_or_none()

        assert new_db_token is not None
        assert new_db_token.user_id == confirmed_user.id


def test_refresh_token_if_user_not_found(
    client, confirmed_user, user_payload, monkeypatch
) -> None:
    """Test that refresh-token returns 401 when token owner is not found."""

    signin_response = client.post(
        f"{PREFIX}/signin",
        data={
            "username": confirmed_user.email,
            "password": user_payload["password"],
        },
    )

    assert signin_response.status_code == 200, signin_response.text
    refresh_token = signin_response.json()["refresh_token"]

    monkeypatch.setattr(
        "src.routes.auth.repository_users.get_user_by_email",
        AsyncMock(return_value=None),
    )

    refresh_response = client.get(
        f"{PREFIX}/refresh-token",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert refresh_response.status_code == 401, refresh_response.text
    assert (
        refresh_response.json()["detail"]
        == HTTPExceptionMessages.could_not_validate_token.value
    )


def test_refresh_token_if_update_failed(
    client, confirmed_user, user_payload, monkeypatch
) -> None:
    """Test that refresh-token returns 401 when token rotation cannot be persisted."""

    signin_response = client.post(
        f"{PREFIX}/signin",
        data={
            "username": confirmed_user.email,
            "password": user_payload["password"],
        },
    )

    assert signin_response.status_code == 200, signin_response.text
    refresh_token = signin_response.json()["refresh_token"]

    monkeypatch.setattr(
        "src.routes.auth.repository_auth.update_refresh_token",
        AsyncMock(return_value=None),
    )

    refresh_response = client.get(
        f"{PREFIX}/refresh-token",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert refresh_response.status_code == 401, refresh_response.text
    assert (
        refresh_response.json()["detail"]
        == HTTPExceptionMessages.could_not_validate_token.value
    )


# =========================================================================
# Confirm email
# =========================================================================
@pytest.mark.asyncio
async def test_confirm_email_if_not_confirmed(client, registered_user) -> None:
    """Test that confirming an unconfirmed email marks the user as confirmed."""

    token = auth_service.create_email_token(payload={"sub": registered_user.email})

    result = client.get(f"{PREFIX}/confirm-email/{token}")

    assert result.status_code == 200, result.text
    data = result.json()
    assert data["message"] == EMAIL_CONFIRMED

    async with TestingSessionLocal() as session:
        db_result = await session.execute(
            select(User).where(User.id == registered_user.id)
        )
        updated_user = db_result.scalar_one()
        assert updated_user.confirmed is True


def test_confirm_email_if_already_confirmed(
    client, registered_user, confirmed_user
) -> None:
    """Test that confirming an already confirmed email returns a status message."""

    token = auth_service.create_email_token(payload={"sub": registered_user.email})

    result = client.get(f"{PREFIX}/confirm-email/{token}")

    assert result.status_code == 200, result.text

    data = result.json()
    assert data["message"] == EMAIL_ALREADY_CONFIRMED


def test_confirm_email_if_user_not_found(client, registered_user) -> None:
    """Test that confirming email for a missing user returns a verification error."""

    token = auth_service.create_email_token(payload={"sub": "email@mail.com"})

    result = client.get(f"{PREFIX}/confirm-email/{token}")

    assert result.status_code == 400, result.text

    data = result.json()
    assert data["detail"] == HTTPExceptionMessages.verification_error.value


# =========================================================================


# =========================================================================
# Request email
# =========================================================================
def test_request_email_if_not_confirmed(client, registered_user, monkeypatch) -> None:
    """Test that an unconfirmed user can request a new confirmation email."""

    body = {"email": registered_user.email}

    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    result = client.post(f"{PREFIX}/request-email", json=body)

    assert result.status_code == 200, result.text
    data = result.json()
    assert data["message"] == CHECK_EMAIL_FOR_CONFIRMATION

    mock_send_email.assert_called_once()
    mock_send_email.call_args.kwargs["token"]
    assert mock_send_email.call_args.kwargs["email"] == registered_user.email
    assert mock_send_email.call_args.kwargs["username"] == registered_user.username


def test_request_email_if_user_not_found(client, registered_user, monkeypatch) -> None:
    """Test that requesting a confirmation email for a missing user returns 404."""

    body = {"email": registered_user.email}

    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    monkeypatch.setattr(
        "src.routes.auth.repository_users.get_user_by_email",
        AsyncMock(return_value=None),
    )

    result = client.post(f"{PREFIX}/request-email", json=body)

    assert result.status_code == 404, result.text

    data = result.json()
    assert data["detail"] == HTTPExceptionMessages.not_found.value
    mock_send_email.assert_not_called()


def test_request_email_if_confirmed(
    client, registered_user, confirmed_user, monkeypatch
) -> None:
    """Test that requesting confirmation for a confirmed user returns a status message only."""

    body = {"email": registered_user.email}

    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    result = client.post(f"{PREFIX}/request-email", json=body)

    assert result.status_code == 200, result.text

    data = result.json()
    assert data["message"] == EMAIL_ALREADY_CONFIRMED
    mock_send_email.assert_not_called()


# =========================================================================


# =========================================================================
# Reset password
# =========================================================================
@pytest.mark.asyncio
async def test_request_password_reset_if_email_exists(
    client, registered_user, monkeypatch
) -> None:
    """Test that password reset request creates a token and sends email."""

    body = {"email": registered_user.email}

    # Replace the real email-sending function with a mock so the test can:
    # 1. avoid sending an actual email during the test run,
    # 2. verify that the route tried to send reset instructions,
    # 3. inspect the generated token that would normally be delivered by email.
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    response = client.post(f"{PREFIX}/password-reset/request", json=body)

    assert response.status_code == 200, response.text
    assert response.json()["message"] == RESET_PASSWORD_EMAIL_EXITS

    # The route should schedule exactly one email for an existing account.
    mock_send_email.assert_called_once()

    # Read back the arguments passed to send_email. This lets the test confirm
    # that the reset flow targeted the expected user and gives access to the
    # raw reset token generated by the application.
    sent_token = mock_send_email.call_args.kwargs["token"]
    assert mock_send_email.call_args.kwargs["email"] == registered_user.email
    assert mock_send_email.call_args.kwargs["username"] == registered_user.username

    # Open a fresh database session and verify the server-side side effect of
    # this endpoint: for an existing user it must create or update a password
    # reset token record in the database.
    result = None
    async with TestingSessionLocal() as session:
        result = await session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == registered_user.id
            )
        )
        reset_token = result.scalar_one_or_none()

        assert reset_token is not None
        # The application stores only the hash of the reset token in the
        # database, not the raw token itself. Therefore the correct way to
        # validate persistence is to hash the token captured from the mocked
        # email call and compare that hash with the stored value.
        assert reset_token.token_hash == auth_service.get_token_hash(sent_token)
        # A newly issued reset token must not be marked as used yet.
        assert reset_token.used_at is None


def test_request_password_reset_if_email_not_exists(client, monkeypatch) -> None:
    """Test that password reset request returns a generic success for unknown email."""

    body = {"email": f"missing.{uuid4().hex}@mail.com"}

    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    response = client.post(f"{PREFIX}/password-reset/request", json=body)

    assert response.status_code == 200, response.text
    assert response.json()["message"] == RESET_PASSWORD_EMAIL_EXITS

    # The route must not send reset instructions for an unknown email.
    mock_send_email.assert_not_called()


def test_reset_password(client, registered_user, monkeypatch) -> None:
    """Test that a valid password reset token can be verified successfully."""

    body = {"email": registered_user.email}

    # Request a fresh reset token through the public endpoint and intercept the
    # outgoing email so the test can reuse the raw token from that message.
    # The database stores only a hash of the token, so the raw value must be
    # captured at the moment the application prepares the email.
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    request_response = client.post(f"{PREFIX}/password-reset/request", json=body)

    assert request_response.status_code == 200, request_response.text
    assert request_response.json()["message"] == RESET_PASSWORD_EMAIL_EXITS
    mock_send_email.assert_called_once()

    reset_password_token = mock_send_email.call_args.kwargs["token"]

    response = client.get(
        f"{PREFIX}/password-reset/verify/{reset_password_token}",
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["message"] == SUCCESS_TO_CREATE_NEW_PASSWORD


@pytest.mark.asyncio
async def test_confirm_reset_password(client, registered_user, monkeypatch) -> None:
    """Test that password reset confirmation updates the password and uses the token."""

    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    request_response = client.post(
        f"{PREFIX}/password-reset/request",
        json={"email": registered_user.email},
    )

    assert request_response.status_code == 200, request_response.text
    mock_send_email.assert_called_once()

    token = mock_send_email.call_args.kwargs["token"]
    new_password = "new_pass_123"

    response = client.patch(
        f"{PREFIX}/password-reset/confirm",
        json={"token": token, "password": new_password},
    )

    assert response.status_code == 204, response.text
    assert response.text == ""

    async with TestingSessionLocal() as session:
        user_result = await session.execute(
            select(User).where(User.id == registered_user.id)
        )
        updated_user = user_result.scalar_one()

        token_result = await session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == registered_user.id
            )
        )
        reset_token = token_result.scalar_one()

        assert auth_service.verify_password(new_password, updated_user.password)
        assert reset_token.used_at is not None


def test_confirm_reset_password_if_user_update_failed(
    client, registered_user, monkeypatch
) -> None:
    """Test that reset confirmation returns 400 when password update fails."""

    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    monkeypatch.setattr(
        "src.routes.auth.repository_users.update_user_password",
        AsyncMock(return_value=None),
    )

    request_response = client.post(
        f"{PREFIX}/password-reset/request",
        json={"email": registered_user.email},
    )

    assert request_response.status_code == 200, request_response.text
    mock_send_email.assert_called_once()

    token = mock_send_email.call_args.kwargs["token"]

    response = client.patch(
        f"{PREFIX}/password-reset/confirm",
        json={"token": token, "password": "new_pass_123"},
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == INVALID_OR_EXPIRED_PASSWORD_RESET_TOKEN
