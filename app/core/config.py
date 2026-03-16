from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    APP_NAME:       str = os.getenv("APP_NAME", "Jarvis")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")   # ← added
    DATABASE_URL:   str = os.getenv("DATABASE_URL", "postgresql+asyncpg://jarvis:jarvis@localhost:5432/jarvis")
    REDIS_URL:      str = os.getenv("REDIS_URL", "redis://localhost:6379")


settings = Settings()