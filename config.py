"""
Configuration — reads from environment variables or a .env file.
"""

import os
from pathlib import Path


def _load_dotenv():
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


_load_dotenv()


class Config:
    # ── Required ──────────────────────────────────────────────────────────────
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # ── Optional ──────────────────────────────────────────────────────────────
    CHECK_INTERVAL_MINUTES: int = int(os.getenv("CHECK_INTERVAL_MINUTES", "2"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── Admin notification (optional) ─────────────────────────────────────────
    # If set, error reports and startup messages go here
    ADMIN_CHAT_ID: str = os.getenv("ADMIN_CHAT_ID", "")
