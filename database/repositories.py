from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models import Application, ApplicationEvent, ApplicationStatus, Document, Job, JobMatch, OutreachEmail


def dedupe_key(external_id: str | None, url: str, company: str, title: str, description: str) -> str:
    normalized_url = url.strip().lower().split("#", 1)[0].rstrip("/")
    clean_description = re.sub(r"\W+", " ", description.lower())[:2000]
    payload = "|".join([external_id or "", normalized_url, company.lower().strip(), title.lower().strip(), clean_description])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def upsert_job(session: Session, data: dict[str, Any]) -> tuple[Job, bool]:
    key = data.get("dedupe_key") or dedupe_key(data.get("external_id"), data["application_url"], data["company"], data["title"], data["description"])
    job = session.scalar(select(Job).where(Job.dedupe_key == key))
    created = job is None
    if job is None:
        job = Job(dedupe_key=key, title=data["title"], company=data["company"], description=data["description"], application_url=data["application_url"], source_name=data.get("source_name", "unknown"))
        session.add(job)
    for field in ("external_id", "required_skills_json", "experience_requirements", "location", "remote_eligibility", "salary", "employment_type", "posting_date", "deadline", "processing_status"):
        if field in data and data[field] is not None:
            setattr(job, field, data[field])
    return job, created


def save_match(session: Session, job: Job, result: dict[str, Any]) -> JobMatch:
    match = session.scalar(select(JobMatch).where(JobMatch.job_id == job.id))
    if match is None:
        match = JobMatch(job_id=job.id, match_score=float(result.get("match_score", 0)), should_apply=bool(result.get("should_apply", False)), result_json=json.dumps(result))
        session.add(match)
    else:
        match.match_score = float(result.get("match_score", 0))
        match.should_apply = bool(result.get("should_apply", False))
        match.result_json = json.dumps(result)
    job.processing_status = "MATCHED" if match.should_apply else "SKIPPED"
    return match


def get_or_create_application(session: Session, job_id: int) -> Application:
    application = session.scalar(select(Application).where(Application.job_id == job_id))
    if application is None:
        application = Application(job_id=job_id)
        session.add(application)
        session.flush()
        session.add(ApplicationEvent(application_id=application.id, event_type="DISCOVERED", details="Application record created"))
    return application


def transition_application(session: Session, application: Application, status: ApplicationStatus | str, details: str = "") -> None:
    new_status = status.value if isinstance(status, ApplicationStatus) else status
    application.status = new_status
    session.add(ApplicationEvent(application_id=application.id, event_type=new_status, details=details))


def save_document(session: Session, job_id: int | None, kind: str, path: str) -> Document:
    document = Document(job_id=job_id, kind=kind, path=path)
    session.add(document)
    return document


def save_outreach(session: Session, **data: Any) -> OutreachEmail:
    existing = session.scalar(select(OutreachEmail).where(OutreachEmail.job_id == data["job_id"], OutreachEmail.contact_role == data["contact_role"], OutreachEmail.recipient_email == data.get("recipient_email")))
    if existing:
        return existing
    item = OutreachEmail(**data)
    session.add(item)
    return item


def summary(session: Session) -> dict[str, int]:
    def count(model: Any) -> int:
        return int(session.scalar(select(func.count()).select_from(model)) or 0)
    return {
        "jobs": count(Job),
        "relevant_jobs": int(session.scalar(select(func.count()).select_from(JobMatch).where(JobMatch.should_apply.is_(True))) or 0),
        "applications": count(Application),
        "confirmed_applications": int(session.scalar(select(func.count()).select_from(Application).where(Application.status == ApplicationStatus.CONFIRMATION_VERIFIED.value)) or 0),
        "pending_applications": int(session.scalar(select(func.count()).select_from(Application).where(Application.status.in_([ApplicationStatus.PENDING_APPROVAL.value, ApplicationStatus.NEEDS_USER_INPUT.value, ApplicationStatus.MANUAL_REVIEW.value]))) or 0),
        "outreach_drafts": int(session.scalar(select(func.count()).select_from(OutreachEmail).where(OutreachEmail.sending_status == "DRAFT")) or 0),
    }
