from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Job


def export_jobs_csv(session: Session, path: str | Path = "storage/jobs.csv") -> Path:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(["id", "company", "title", "location", "source", "url", "status"])
        for job in session.scalars(select(Job)):
            writer.writerow([job.id, job.company, job.title, job.location or "", job.source_name, job.application_url, job.processing_status])
    return path
