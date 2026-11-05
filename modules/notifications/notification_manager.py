from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database.models import Notification
from modules.notifications.telegram_bot import TelegramBot


class NotificationManager:
    def __init__(self, bot: TelegramBot | None = None):
        self.bot = bot or TelegramBot()

    def enqueue(self, session: Session, kind: str, payload: dict) -> Notification:
        item = Notification(channel="telegram", kind=kind, payload_json=json.dumps(payload)); session.add(item); session.flush()
        text = payload.get("text", json.dumps(payload, indent=2))
        if self.bot.send(text):
            item.status, item.sent_at = "SENT", datetime.now(timezone.utc)
        return item

    def daily_summary(self, summary: dict[str, int], failures: dict[str, str] | None = None) -> str:
        return "Daily job search summary\n\n" + "\n".join(f"{key.replace('_', ' ').title()}: {value}" for key, value in summary.items()) + ("\n\nScraper failures:\n" + "\n".join(f"- {key}: {value}" for key, value in (failures or {}).items()) if failures else "")
