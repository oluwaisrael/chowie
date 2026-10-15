from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")
    database_url: str = "postgresql+psycopg://oriade:oriade@localhost:5432/oriade"
    redis_url: str = "redis://localhost:6379/0"
    app_origin: str = "http://localhost:3000"
    environment: str = "development"
    whatsapp_number: str = "2348066514361"
    session_days: int = 7
    sentry_dsn: str = ""
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    s3_public_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""


@lru_cache
def settings():
    return Settings()
