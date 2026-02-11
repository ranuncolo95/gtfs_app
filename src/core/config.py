from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")


    # Shiny montata dentro FastAPI (single-port)
    shiny_url: str = "/shiny/"

    # MapTiler
    maptiler_api_key: str = ""
    maptiler_geocode_limit: int = 5
    maptiler_timeout_s: float = 5.0

    @field_validator("shiny_url", mode="before")
    @classmethod
    def normalize_shiny_url(cls, v):
        v = (v or "/shiny/").strip()
        # per path relativi: assicurati che finisca con /
        if v.startswith("/"):
            return v if v.endswith("/") else v + "/"
        # per url assoluti
        return v if v.endswith("/") else v + "/"
