from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки бота. Читаются из переменных окружения и файла .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: SecretStr
    backend_url: HttpUrl
    backend_timeout_seconds: float = 10.0
    db_path: str = "bot_state.sqlite3"
    log_level: str = "INFO"
    reminder_interval_hours: float = 24.0
    reminder_check_seconds: float = 3600.0
