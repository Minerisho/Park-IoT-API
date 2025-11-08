# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "API Parqueadero Inteligente"
    description: str = "API con IA para usar con una ESP32 + Front-end para un parqueadero inteligente. Proyecto de IoT UIS 2025-2."
    debug: bool = True
    db_url: str = "sqlite:///./app.db"
    cors_origins: list[str] = ["*"]   # Lista de orígenes permitidos
    api_key_salt: str = "change-me"   # la key de la api

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_csv(cls, v):
        # Permite CORS_ORIGINS="http://localhost:5173,http://localhost:3000" o "*"
        if isinstance(v, str):
            v = v.strip()
            if v == "*":
                return ["*"]
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

@lru_cache
def get_settings() -> Settings:
    return Settings()
