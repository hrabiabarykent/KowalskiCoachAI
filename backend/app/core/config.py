from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "KowalskiCoach AI Multisport"
    GEMINI_API_KEY: Optional[str] = None
    DATABASE_URL: str = "sqlite:///./users.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
