from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    APP_NAME:             str  = os.getenv("APP_NAME", "Jarvis")
    DEBUG:                bool = os.getenv("DEBUG", "false").lower() == "true"
    GEMINI_API_KEY:       str  = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY:       str  = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL:         str  = os.getenv("DATABASE_URL", "postgresql+asyncpg://jarvis:jarvis@localhost:5432/jarvis")
    REDIS_URL:            str  = os.getenv("REDIS_URL", "redis://localhost:6379")
    GOOGLE_MAPS_API_KEY:  str  = os.getenv("GOOGLE_MAPS_API_KEY", "")

    # Twilio
    TWILIO_ACCOUNT_SID:   str  = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN:    str  = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER:  str  = os.getenv("TWILIO_PHONE_NUMBER", "")
    YOUR_PHONE_NUMBER:    str  = os.getenv("YOUR_PHONE_NUMBER", "")

    # ElevenLabs
    ELEVENLABS_API_KEY:   str  = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID:  str  = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")


settings = Settings()