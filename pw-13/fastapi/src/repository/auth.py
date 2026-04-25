from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken


# Create and persist a refresh token row for a user.
async def add_refresh_token(
    token: str, user_id: int, db: AsyncSession
) -> RefreshToken:
    """Store refresh token in DB and return created token row."""
    record = RefreshToken(rf_token=token, user_id=user_id)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record

# Find a refresh token row by token value.
async def get_refresh_token_by_token(
    token: str, db: AsyncSession
) -> RefreshToken | None:
    """Return refresh token row by token value, or None if not found."""
    stmt = select(RefreshToken).filter_by(rf_token=token)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# Rotate stored refresh token value.
async def update_refresh_token(
    old_token: str, new_token: str, db: AsyncSession
) -> RefreshToken | None:
    """Rotate an existing refresh token value and return updated token row."""
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
    """Delete all refresh token rows for the provided user id."""
    stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
    await db.execute(stmt)
    await db.commit()


# Delete one refresh token by value.
async def delete_refresh_token_by_token(token: str, db: AsyncSession) -> bool:
    """Delete refresh token row by token value and return deletion status."""
    stmt = delete(RefreshToken).where(RefreshToken.rf_token == token)
    result = await db.execute(stmt)
    await db.commit()
    # Return True or False whether something was deleted/updated.
    return (result.rowcount or 0) > 0 # how many rows did SQL grab
