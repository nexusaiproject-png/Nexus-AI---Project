from dataclasses import dataclass
import os


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/nexus.db")
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str = _database_url()


def get_settings() -> Settings:
    return Settings()
