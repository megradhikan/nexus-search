from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    github_token: str = ""
    notion_token: str = ""
    github_repos: list[str] = []
    database_url: str = "postgresql://nexus:nexus@localhost:5432/nexusdb"
    polling_interval_minutes: int = 30
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
