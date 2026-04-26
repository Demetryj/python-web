import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.schemas.users import UserResponse
from src.services.auth import auth_service
from src.config.rate_limiters import users_base_limiter, user_update_avatar_limiter
from src.config.settings import settings
from src.database.db import get_db
from src.repository import users as repository_users

router = APIRouter(prefix="/user", tags=["user"])

cloudinary.config(
    cloud_name=settings.CLOUDINARY_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


@router.get(
    "/me",
    response_model=UserResponse,
    response_description="Success",
    dependencies=[Depends(RateLimiter(limiter=users_base_limiter))],
)
async def get_me(user: User = Depends(auth_service.get_current_user)) -> UserResponse:
    """Return current authenticated user profile."""
    return user


@router.patch(
    "/update-avatar",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(limiter=user_update_avatar_limiter))],
)
async def update_avatar(
    file: UploadFile = File(),
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Upload user's avatar to Cloudinary and save the new avatar URL."""
    public_id = f"pw_13/{user.email}"

    # Upload the new avatar to Cloudinary under a stable user-specific public id.
    try:
        res = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload avatar",
        ) from err

    # Build a fixed-size image URL for storing and returning in the user profile.
    res_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=res.get("version")
    )

    updated_user = await repository_users.update_avatar_url(user.email, res_url, db)
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return updated_user
