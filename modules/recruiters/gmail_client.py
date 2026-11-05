from __future__ import annotations

import base64
from email.message import EmailMessage
from pathlib import Path

from config import Settings


class GmailDraftClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()

    @property
    def configured(self) -> bool:
        return bool(self.settings.gmail_client_id and self.settings.gmail_client_secret and Path(self.settings.gmail_token_path).exists())

    def create_draft(self, to: str, subject: str, body: str, attachment: str | None = None) -> str:
        if not self.configured:
            raise RuntimeError("Gmail OAuth is not configured; save the outreach as a local draft instead")
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        credentials = Credentials.from_authorized_user_file(self.settings.gmail_token_path, ["https://www.googleapis.com/auth/gmail.compose"])
        message = EmailMessage(); message["To"] = to; message["From"] = self.settings.gmail_user; message["Subject"] = subject; message.set_content(body)
        if attachment and Path(attachment).exists():
            data = Path(attachment).read_bytes(); message.add_attachment(data, maintype="application", subtype="pdf", filename=Path(attachment).name)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = build("gmail", "v1", credentials=credentials).users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        return str(draft["id"])
