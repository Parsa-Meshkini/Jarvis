from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Jarvis"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://jarvis:jarvis@localhost:5432/jarvis"
    redis_url: str = "redis://localhost:6379"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Phase 2 — tools
    google_maps_api_key: str = ""
    google_calendar_credentials: str = ""
    google_calendar_id: str = ""
    google_calendar_timezone: str = "America/Toronto"

    # Phase 4 — voice
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    elevenlabs_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()