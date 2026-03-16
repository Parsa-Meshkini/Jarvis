# app/core/config.py
from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    APP_NAME:        str  = os.getenv("APP_NAME", "Jarvis")
    DEBUG:           bool = os.getenv("DEBUG", "false").lower() == "true"
    GEMINI_API_KEY:  str  = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY:  str  = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL:    str  = os.getenv("DATABASE_URL", "postgresql+asyncpg://jarvis:jarvis@localhost:5432/jarvis")
    REDIS_URL:       str  = os.getenv("REDIS_URL", "redis://localhost:6379")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")


settings = Settings()