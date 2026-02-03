"""
DealSnap - Configuration Settings
Environment-based configuration using pydantic-settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "DealSnap"
    app_version: str = "2.0.0"
    debug: bool = False

    # Server
    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    # Default to specific origins in production, allow comma-separated string from env
    cors_origins: str | list[str] = ["http://localhost:8000"]

    @property
    def cors_origins_list(self) -> list[str]:
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # OAuth/SSO (Google)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    oauth_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Session/JWT
    # Use environment variable in production! Auto-generate for dev if missing.
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-this-in-prod")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Frontend
    frontend_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Warn if using default secret key in apparent production
        if self.secret_key == "dev-secret-key-change-this-in-prod" and not self.debug:
             import secrets
             # Auto-generate a strong key for this session if generic default found and not debug
             # This prevents insecure defaults in deployment, though session persistence will valid
             self.secret_key = secrets.token_urlsafe(32)


settings = Settings()

