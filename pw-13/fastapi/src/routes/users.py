from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

from src.entity.models import User
from src.schemas.users import UserResponse
from src.services.auth import auth_service
from src.config.rate_limiters import users_base_limiter

router = APIRouter(prefix="/user", tags=["user"])


@router.get(
    "/me",
    response_model=UserResponse,
    response_description="Success",
    dependencies=[Depends(RateLimiter(limiter=users_base_limiter))],
)
async def get_me(user: User = Depends(auth_service.get_current_user)) -> UserResponse:
    """Return current authenticated user profile."""
    return user
