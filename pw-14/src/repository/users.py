"""Database operations for user accounts."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
import logging

from src.entity.models import User, PasswordResetToken
from src.schemas.users import UserShchema
from src.schemas.auth import ResetPasswordSchema

logger = logging.getLogger(__name__)


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """Return a user by email.

    :param email: User email address.
    :type email: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: User instance when found, otherwise ``None``.
    :rtype: User | None
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    return user.scalar_one_or_none()


async def create_user(body: UserShchema, db: AsyncSession) -> User:
    """Create a new user account.

    The function tries to fetch a Gravatar image for the provided email and
    stores it as the initial avatar when available.

    :param body: User registration payload.
    :type body: UserShchema
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Created user instance.
    :rtype: User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        logger.warning("Failed to fetch Gravatar for %s: %s", body.email, err)

    user_data = body.model_dump(include={"username", "email", "password"})
    new_user = User(**user_data, avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def confirm_email(email: str, db: AsyncSession) -> None:
    """Mark a user email as confirmed.

    :param email: User email address.
    :type email: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: ``None``.
    :rtype: None
    """
    user: User | None = await get_user_by_email(email=email, db=db)
    if user is None:
        return
    user.confirmed = True
    await db.commit()
    await db.refresh(user)


async def update_avatar_url(
    email: str,
    avatar_url: str,
    db: AsyncSession,
) -> User | None:
    """Update a user's avatar URL.

    :param email: User email address.
    :type email: str
    :param avatar_url: New avatar image URL.
    :type avatar_url: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Updated user instance when found, otherwise ``None``.
    :rtype: User | None
    """
    user = await get_user_by_email(email=email, db=db)
    if user is None:
        return None
    user.avatar = avatar_url
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_password(
    email: str,
    hashed_password: str,
    db: AsyncSession,
) -> User | None:
    """Update a user's password hash.

    :param email: User email address.
    :type email: str
    :param hashed_password: New hashed password value.
    :type hashed_password: str
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :return: Updated user instance when found, otherwise ``None``.
    :rtype: User | None
    """
    user = await get_user_by_email(email=email, db=db)
    if user is None:
        return None
    user.password = hashed_password
    await db.commit()
    await db.refresh(user)
    return user
