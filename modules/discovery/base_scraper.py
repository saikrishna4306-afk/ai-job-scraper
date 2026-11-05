from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JobRecord:
    title: str
    company: str
    description: str
    application_url: str
    source_name: str
    external_id: str | None = None
    required_skills: list[str] = field(default_factory=list)
    experience_requirements: str | None = None
    location: str | None = None
    remote_eligibility: str | None = None
    salary: str | None = None
    employment_type: str | None = None
    posting_date: datetime | None = None
    deadline: datetime | None = None
    discovered_at: datetime = field(default_factory=now_utc)

    @property
    def fingerprint(self) -> str:
        value = "|".join((self.external_id or "", self.application_url, self.company, self.title, self.description[:2000]))
        return hashlib.sha256(value.lower().encode()).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        import json
        result["required_skills_json"] = json.dumps(result.pop("required_skills"))
        return result


class SourceAdapter(Protocol):
    name: str

    def fetch(self) -> list[JobRecord]: ...


def normalize_job(raw: dict[str, Any], source_name: str) -> JobRecord:
    """Normalize common dict shapes while keeping scraped content as data."""
    title = str(raw.get("title") or raw.get("job_title") or "Untitled role").strip()
    company = str(raw.get("company") or raw.get("company_name") or "Unknown company").strip()
    description = str(raw.get("description") or raw.get("job_description") or "").strip()
    url = str(raw.get("application_url") or raw.get("job_url") or raw.get("url") or "").strip()
    remote_text = f"{raw.get('remote_eligibility') or ''} {raw.get('location') or ''} {description}".lower()
    remote = "remote" if "remote" in remote_text or "work from home" in remote_text else "not specified"
    return JobRecord(title=title, company=company, description=description, application_url=url, source_name=source_name, external_id=str(raw.get("id")) if raw.get("id") else None, required_skills=list(raw.get("required_skills") or []), experience_requirements=raw.get("experience_requirements"), location=raw.get("location"), remote_eligibility=remote, salary=raw.get("salary"), employment_type=raw.get("employment_type"))


def deduplicate_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    seen: set[str] = set()
    result: list[JobRecord] = []
    for job in jobs:
        key = job.external_id or job.application_url.lower().split("#", 1)[0].rstrip("/")
        if not key:
            key = re.sub(r"\W+", " ", f"{job.company} {job.title} {job.description[:500]}".lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(job)
    return result
