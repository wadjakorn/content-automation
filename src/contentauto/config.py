from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    fernet_key: str
    anthropic_api_key: str
    anthropic_model: str = "claude-opus-4-8"
    yt_client_id: str
    yt_client_secret: str
    yt_redirect_uri: str
    validate_verdicts: bool = True


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
