"""Typed, secret-safe application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
STORAGE_DIR = ROOT_DIR / "storage"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.lower().strip() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    timezone: str = "Asia/Kolkata"
    log_level: str = "INFO"
    database_url: str = "sqlite:///storage/job_agent.db"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_timeout_seconds: int = 300
    gmail_user: str = ""
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_token_path: str = "storage/gmail_token.json"
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_storage_bucket: str = ""
    remote_only: bool = True
    worldwide_remote: bool = False
    india_remote: bool = True
    job_lookback_hours: int = 24
    minimum_match_score: int = 7
    max_jobs_per_platform: int = 20
    auto_apply_enabled: bool = False
    require_approval: bool = True
    outreach_auto_send: bool = False
    follow_up_days: int = 7
    storage_dir: Path = field(default=STORAGE_DIR)

    @classmethod
    def load(cls, env_file: Path | None = None) -> "Settings":
        _load_dotenv(env_file or ROOT_DIR / ".env")
        value = cls(
            app_env=os.getenv("APP_ENV", "development"), timezone=os.getenv("TIMEZONE", "Asia/Kolkata"),
            log_level=os.getenv("LOG_LEVEL", "INFO"), database_url=os.getenv("DATABASE_URL") or "sqlite:///storage/job_agent.db",
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""), gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""), telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            telegram_timeout_seconds=_int("TELEGRAM_TIMEOUT_SECONDS", 300), gmail_user=os.getenv("GMAIL_USER", ""),
            gmail_client_id=os.getenv("GMAIL_CLIENT_ID", ""), gmail_client_secret=os.getenv("GMAIL_CLIENT_SECRET", ""),
            gmail_token_path=os.getenv("GMAIL_TOKEN_PATH", "storage/gmail_token.json"), supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_key=os.getenv("SUPABASE_KEY", ""), supabase_storage_bucket=os.getenv("SUPABASE_STORAGE_BUCKET", ""),
            remote_only=_bool("REMOTE_ONLY", True), worldwide_remote=_bool("WORLDWIDE_REMOTE", False), india_remote=_bool("INDIA_REMOTE", True),
            job_lookback_hours=_int("JOB_LOOKBACK_HOURS", 24), minimum_match_score=max(1, min(10, _int("MINIMUM_MATCH_SCORE", 7))),
            max_jobs_per_platform=max(1, _int("MAX_JOBS_PER_PLATFORM", 20)), auto_apply_enabled=_bool("AUTO_APPLY_ENABLED", False),
            require_approval=_bool("REQUIRE_APPROVAL", True), outreach_auto_send=_bool("OUTREACH_AUTO_SEND", False), follow_up_days=max(1, _int("FOLLOW_UP_DAYS", 7)),
        )
        value.storage_dir.mkdir(parents=True, exist_ok=True)
        return value

    def status(self) -> dict[str, Any]:
        return {
            "AI": "Gemini configured" if self.gemini_api_key else "Mock mode (GEMINI_API_KEY missing)",
            "Telegram": "Configured" if self.telegram_bot_token and self.telegram_chat_id else "Disabled",
            "Gmail": "OAuth credentials configured" if self.gmail_client_id and self.gmail_client_secret else "Draft integration disabled",
            "Database": "PostgreSQL/Supabase" if self.database_url.startswith(("postgres", "postgresql")) else "SQLite local",
            "Application mode": "Authorized automation" if self.auto_apply_enabled and not self.require_approval else "Assisted / approval required",
            "Outreach mode": "Authorized sending" if self.outreach_auto_send else "Draft-only",
        }


settings = Settings.load()
