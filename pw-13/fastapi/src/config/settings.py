"""
Application settings managed via Pydantic Settings.
In this setup, environment variables are expected to be injected by
Docker Compose (`environment` / `env_file` on container level), not read
directly from a local `.env` file inside Python code.
"""

from pydantic import computed_field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Schema for required env variables and derived application values."""

    # model_config = SettingsConfigDict(
    #     env_file=".env",
    #     env_file_encoding="utf-8",
    #     extra="ignore",
    # )

    # We use env_file=None because Docker Compose already injects env vars
    # into the container process. This avoids coupling to a local .env path
    # inside the container and keeps configuration centralized in compose.
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # Properties (fields, attributes) can be in either lower or upper case.
    # Each of them can have a default value..
    psg_db_user: str
    psg_db_password: str
    psg_db_name: str
    psg_db_domain: str
    psg_db_port: int

    secret_key: str
    hash_algorithm: str = "HS256"

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 2525
    MAIL_SERVER: str = "sandbox.smtp.mailtrap.io"

    REDIS_DOMAIN: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @computed_field
    @property
    def DB_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.psg_db_user}:{self.psg_db_password}"
            f"@{self.psg_db_domain}:{self.psg_db_port}/{self.psg_db_name}"
        )


settings = Settings()
