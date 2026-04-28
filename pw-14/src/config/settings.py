"""
Application settings managed via Pydantic Settings.
In this setup, environment variables are expected to be injected by
Docker Compose (`environment` / `env_file` on container level), not read
directly from a local `.env` file inside Python code.
"""

from pathlib import Path

from pydantic import computed_field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    The settings object contains database, JWT, email, Redis, and Cloudinary
    configuration values required by the API.
    """

    # model_config = SettingsConfigDict(
    #     env_file=BASE_DIR / ".env",
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
    
    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: int
    CLOUDINARY_API_SECRET: str

    @computed_field
    @property
    def DB_URL(self) -> str:
        """Build the SQLAlchemy async PostgreSQL connection URL.

        :return: PostgreSQL connection URL for ``asyncpg``.
        :rtype: str
        """
        return (
            f"postgresql+asyncpg://{self.psg_db_user}:{self.psg_db_password}"
            f"@{self.psg_db_domain}:{self.psg_db_port}/{self.psg_db_name}"
        )


settings = Settings()
