import os
from dataclasses import dataclass


@dataclass
class Config:
    bot_token: str
    database_url: str
    daily_bonus_amount: int
    referral_bonus_amount: int
    admin_ids: set[int]


def _normalize_database_url(url: str) -> str:
    """Ensure the URL uses the asyncpg driver, regardless of how the
    hosting provider (e.g. Railway) formats DATABASE_URL."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN environment variable is required")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    daily_bonus_amount = int(os.getenv("DAILY_BONUS_AMOUNT", "100"))
    referral_bonus_amount = int(os.getenv("REFERRAL_BONUS_AMOUNT", "50"))

    admin_ids_raw = os.getenv("ADMIN_IDS", "")
    admin_ids = {
        int(chunk.strip())
        for chunk in admin_ids_raw.split(",")
        if chunk.strip().lstrip("-").isdigit()
    }

    return Config(
        bot_token=bot_token,
        database_url=_normalize_database_url(database_url),
        daily_bonus_amount=daily_bonus_amount,
        referral_bonus_amount=referral_bonus_amount,
        admin_ids=admin_ids,
    )
