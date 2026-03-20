from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # App settings
    app_name: str = "ChatApp"

    # Security
    secret_key: str = Field(..., env="CHATAPP_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="CHATAPP_JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60 * 24 * 7, env="CHATAPP_ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(30, env="CHATAPP_REFRESH_TOKEN_EXPIRE_DAYS")

    # Database
    database_url: str = Field("sqlite:///./chatapp.db", env="DATABASE_URL")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
