from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
import logging

from src.entity.models import User
from src.schemas.users import UserShchema


logger = logging.getLogger(__name__)


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """Return a user by email, or None when no user exists."""
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    return user.scalar_one_or_none()


async def create_user(body: UserShchema, db: AsyncSession) -> User:
    """Create a new user and try to enrich profile with a Gravatar URL."""
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

