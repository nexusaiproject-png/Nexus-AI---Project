from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/nexus.db")


def get_settings() -> Settings:
    return Settings()
