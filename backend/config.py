"""Environment-based configuration."""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_research_model: str = "gpt-4o"

    enable_web_search: bool = True
    web_search_tool: str = "web_search"

    research_max_tokens: int = 7000
    structure_max_tokens: int = 7000

    default_currency: str = "USD"
    default_min_hotel_stars: int = 3
    admin_margin: float = 0.28
    default_package_count: int = 3
    max_package_count: int = 10

    backend_url: str = "http://localhost:8000"

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key and not self.openai_api_key.startswith("sk-proj-xxxx"))


settings = Settings()
