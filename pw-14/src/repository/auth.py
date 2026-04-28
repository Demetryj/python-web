"""Database operations for refresh tokens and password reset tokens."""

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken, PasswordResetToken


# Create and persist a refresh token row for a user.
async def add_refresh_token(token: str, user_id: int, db: AsyncSession) -> RefreshToken:
    """Store a refresh token.

    :param token: Raw refresh token value.
    :type token: str
    :param user_id: Owner user identifier.
    :type user_id: int
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Created refresh token row.
    :rtype: RefreshToken
    """
    record = RefreshToken(rf_token=token, user_id=user_id)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


# Find a refresh token row by token value.
async def get_refresh_token_by_token(
    token: str, db: AsyncSession
) -> RefreshToken | None:
    """Return a refresh token row by token value.

    :param token: Raw refresh token value.
    :type token: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Refresh token row when found, otherwise ``None``.
    :rtype: RefreshToken | None
    """
    stmt = select(RefreshToken).filter_by(rf_token=token)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# Rotate stored refresh token value.
async def update_refresh_token(
    old_token: str, new_token: str, db: AsyncSession
) -> RefreshToken | None:
    """Replace an existing refresh token value.

    :param old_token: Current refresh token value.
    :type old_token: str
    :param new_token: New refresh token value.
    :type new_token: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Updated refresh token row when found, otherwise ``None``.
    :rtype: RefreshToken | None
    """
    stmt = select(RefreshToken).filter_by(rf_token=old_token)
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()

    if db_token:
        db_token.rf_token = new_token
        await db.commit()
        await db.refresh(db_token)

    return db_token


# Delete all refresh tokens belonging to a user.
async def delete_refresh_tokens_by_user_id(user_id: int, db: AsyncSession) -> None:
    """Delete all refresh tokens for a user.

    :param user_id: Owner user identifier.
    :type user_id: int
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: ``None``.
    :rtype: None
    """
    stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
    await db.execute(stmt)
    await db.commit()


# Delete one refresh token by value.
async def delete_refresh_token_by_token(token: str, db: AsyncSession) -> bool:
    """Delete one refresh token by token value.

    :param token: Raw refresh token value.
    :type token: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: ``True`` when a row was deleted, otherwise ``False``.
    :rtype: bool
    """
    stmt = delete(RefreshToken).where(RefreshToken.rf_token == token)
    result = await db.execute(stmt)
    await db.commit()
    # Return True or False whether something was deleted/updated.
    return (result.rowcount or 0) > 0  # how many rows did SQL grab


# Create or rotate a one-time password reset token record for a user.
async def add_password_reset_token(
    user_id: int, token_hash: str, expires_at: datetime, db: AsyncSession
) -> None:
    """Store or rotate a password reset token record.

    :param user_id: Owner user identifier.
    :type user_id: int
    :param token_hash: Deterministic hash of the raw reset token.
    :type token_hash: str
    :param expires_at: Reset token expiration timestamp.
    :type expires_at: datetime
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: ``None``.
    :rtype: None
    """
    # Keep at most one active password reset token row per user.
    stmt = select(PasswordResetToken).filter_by(user_id=user_id)
    result = await db.execute(stmt)
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        # First reset request for this user: create a new token row.
        reset_token = PasswordResetToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        db.add(reset_token)

    # Reissue flow: overwrite token hash and expiration with the latest values.
    reset_token.user_id = user_id
    reset_token.token_hash = token_hash
    reset_token.expires_at = expires_at
    reset_token.used_at = None

    await db.commit()
    await db.refresh(reset_token)


# Find stored password reset token row by deterministic token hash.
async def get_password_reset_token(
    token_hash: str, db: AsyncSession
) -> PasswordResetToken | None:
    """Return a password reset token row by token hash.

    :param token_hash: Deterministic hash of the raw reset token.
    :type token_hash: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Password reset token row when found, otherwise ``None``.
    :rtype: PasswordResetToken | None
    """
    stmt = select(PasswordResetToken).filter_by(token_hash=token_hash)
    result = await db.execute(stmt)
    reset_token = result.scalar_one_or_none()
    return reset_token


# Mark password reset token as used after successful password change.
async def update_used_status_password_reset_token(token_hash: str, db: AsyncSession):
    """Mark a password reset token as used.

    :param token_hash: Deterministic hash of the raw reset token.
    :type token_hash: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: ``None``.
    :rtype: None
    """
    db_token_obj = await get_password_reset_token(token_hash=token_hash, db=db)
    if not db_token_obj:
        return
    db_token_obj.used_at = datetime.now()
    await db.commit()
    await db.refresh(db_token_obj)
