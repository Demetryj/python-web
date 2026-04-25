"""
Application settings managed via Pydantic Settings.
In this setup, environment variables are expected to be injected by
Docker Compose (`environment` / `env_file` on container level), not read
directly from a local `.env` file inside Python code.
"""

from pydantic import computed_field
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
    model_config = SettingsConfigDict(
        env_file=None
    )

    db_user: str
    db_password: str
    db_name: str
    db_domain: str
    db_port: int
    secret_key: str

    @computed_field
    @property
    def DB_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_domain}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
