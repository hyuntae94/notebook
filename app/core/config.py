"""Application settings, loaded from environment / .env via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Values are read from environment variables (case-insensitive) and an
    optional ``.env`` file. See ``.env.example`` for the supported keys.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "fast_back"
    environment: str = "development"
    debug: bool = True

    # Comma-separated list of allowed CORS origins, e.g. "http://localhost:3000".
    cors_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the ``.env`` file is parsed once per process. Override in tests
    via ``app.dependency_overrides[get_settings]``.
    """
    return Settings()
