"""Centralized Redis-backed rate limiter definitions for API routes."""

from redis import Redis
from pyrate_limiter import Duration, Limiter, Rate, RedisBucket

from src.config.settings import settings

redis_client = Redis(
    host=settings.REDIS_DOMAIN,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


def make_limiter(rate: Rate, bucket: str) -> Limiter:
    """Create a Redis-backed limiter for a specific rate and bucket namespace."""
    redis_bucket = RedisBucket.init([rate], redis_client, bucket)
    return Limiter(redis_bucket)


# AUTH
# base (to the entire route /auth)
auth_base_limiter = make_limiter(Rate(60, Duration.MINUTE), "auth_base")

# stricter per route
auth_signup_limiter = make_limiter(Rate(40, Duration.MINUTE), "auth_signup")
auth_refresh_token_limiter = make_limiter(Rate(10, Duration.MINUTE), "auth_refresh_token")
auth_confirm_email_limiter = make_limiter(Rate(10, Duration.MINUTE), "auth_confirm_email")
auth_request_email_limiter = make_limiter(
    Rate(3, Duration.MINUTE * 5), "auth_request_email"
)

# CONTACTS
# contacts routes - base
contacts_base_limiter = make_limiter(Rate(10, Duration.MINUTE), "contacts_base")

# USER
# users routes -  base
users_base_limiter = make_limiter(Rate(10, Duration.MINUTE), "users_base")
