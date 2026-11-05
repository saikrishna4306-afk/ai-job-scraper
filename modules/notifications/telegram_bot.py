from __future__ import annotations

import json
import urllib.parse
import urllib.request

from config import Settings


class TelegramBot:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()

    @property
    def configured(self) -> bool:
        return bool(self.settings.telegram_bot_token and self.settings.telegram_chat_id)

    def send(self, text: str, chat_id: str | None = None) -> bool:
        if not self.configured:
            return False
        payload = urllib.parse.urlencode({"chat_id": chat_id or self.settings.telegram_chat_id, "text": text}).encode()
        request = urllib.request.Request(f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage", data=payload, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.status == 200
        except Exception:
            return False

    def format_new_job(self, company: str, role: str, location: str, score: float, skills: list[str], url: str, remote_eligibility: str = "", salary: str = "", shift_type: str = "", currency: str = "") -> str:
        parts = [
            f"🚀 New Remote Job Found",
            f"\nCompany: {company}",
            f"Role: {role}",
            f"Location: {location}",
            f"Match Score: {score}/10"
        ]
        if remote_eligibility:
            parts.append(f"Remote Eligibility: {remote_eligibility}")
        if salary:
            parts.append(f"Compensation: {salary} {currency}".strip())
        if shift_type and shift_type != "Unknown":
            parts.append(f"Shift Type: {shift_type}")
        parts.append(f"\nMatching skills:\n" + "\n".join(f"- {skill}" for skill in skills) + f"\n\nApply link: {url}")
        return "\n".join(parts)

    def format_unknown_question(self, company: str, role: str, question: str, options: list[str]) -> str:
        return f"⚠️ Application Needs Your Input\n\nCompany: {company}\nRole: {role}\n\nQuestion:\n{question}\n\nOptions:\n" + "\n".join(f"- {option}" for option in options)

    @staticmethod
    def allowed_command(command: str) -> bool:
        return command.strip().split()[0].lower() in {"/start", "/status", "/jobs", "/applications", "/pending", "/summary", "/help"} if command.strip() else False
