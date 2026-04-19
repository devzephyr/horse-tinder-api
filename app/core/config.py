from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://horsetinder:password@localhost:5432/horsetinder"

    @property
    def async_database_url(self) -> str:
        """Ensure the URL uses the asyncpg driver, stripping libpq-only params."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Strip query params (sslmode, channel_binding, etc. are libpq-only)
        base = url.split("?")[0]
        # Re-add SSL if the original URL requested it
        if "sslmode=" in url or "ssl=" in url:
            base += "?ssl=require"
        return base

    ACCESS_TOKEN_SECRET: str = "dev-access-secret-change-me-in-production-min-32-bytes"
    REFRESH_TOKEN_SECRET: str = "dev-refresh-secret-change-me-in-production-min-32-bytes"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    RATE_LIMIT_STORAGE_URI: str = "memory://"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
