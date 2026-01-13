 # backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./linguee_like.db"  # pour commencer en local

    class Config:
        env_file = ".env"

settings = Settings()