from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    APP_NAME = os.getenv("APP_NAME")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")

settings = Settings()