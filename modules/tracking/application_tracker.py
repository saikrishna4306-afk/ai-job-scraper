from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Application, Job


def export_applications_csv(session: Session, path: str | Path = "storage/applications.csv") -> Path:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(["application_id", "job_id", "company", "title", "status", "submitted_at", "confirmation_id"])
        for application in session.scalars(select(Application)):
            writer.writerow([application.id, application.job_id, application.job.company, application.job.title, application.status, application.submitted_at or "", application.confirmation_id or ""])
    return path
