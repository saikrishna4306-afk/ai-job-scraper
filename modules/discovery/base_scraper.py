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
    country: str | None = None
    remote_eligibility: str | None = None  # not_remote, india_remote, worldwide_remote, hybrid_india, hybrid_other, hybrid_onsite_india, hybrid_onsite_other, relocation_required, ineligible
    shift_type: str | None = None  # fixed, rotational, night_shift, overlap_supported, flexible
    work_hours: str | None = None
    expected_overlap: str | None = None
    salary: str | None = None
    salary_classification: str | None = None  # unpaid, paid_disclosed, paid_confirmed, compensation_unclear
    currency: str | None = None
    frequency: str | None = None
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
    location = str(raw.get("location") or raw.get("job_location") or "").strip()
    country = str(raw.get("country") or raw.get("job_country") or "").strip()
    remote_text = f"{raw.get('remote_eligibility') or ''} {location} {description} {title}".lower()
    # Detect worldwide remote first (strongest signal)
    worldwide_signals = ("worldwide", "anywhere in the world", "global remote", "work from anywhere", "global opportunity")
    india_signals = ("work from home", "remote", "wfh")
    if raw.get("worldwide_remote") or any(sig in remote_text for sig in worldwide_signals):
        remote = "worldwide_remote"
    elif any(sig in remote_text for sig in india_signals):
        remote = "india_remote"
    elif "hybrid" in location.lower():
        remote = "hybrid_india"
    elif "onsite" in location.lower() or "on site" in location.lower() or "on-site" in location.lower():
        remote = "hybrid_onsite_india" if "india" in (location or "").lower() or (country or "").lower() == "india" else "hybrid_onsite_other"
    else:
        remote = "not_remote"
    salary = str(raw.get("salary") or raw.get("compensation") or raw.get("min_amount") or "").strip() or None
    salary_lower = (salary or "").lower()
    salary_text = salary_lower + " " + description.lower()
    # Detect salary classification
    if any(k in salary_text for k in ("$", "usd", "€", "eur", "£", "gbp", "₹", "inr", "lakh", "stipend", "per year", "per month", "yearly", "monthly", "/year", "/month", "/yr", "/mo")):
        salary_classification = "paid_disclosed"
    elif "unpaid" in salary_text or "volunteer" in salary_text:
        salary_classification = "unpaid"
    else:
        salary_classification = "compensation_unclear"
    # Detect currency from salary text
    currency = raw.get("currency") or ("USD" if ("$" in salary_text or "usd" in salary_text) else ("EUR" if ("€" in salary_text or "eur" in salary_text) else ("GBP" if ("£" in salary_text or "gbp" in salary_text) else ("INR" if ("₹" in salary_text or "inr" in salary_text or "lakh" in salary_text) else None))))
    # Detect frequency
    frequency = raw.get("frequency") or ("yearly" if any(k in salary_text for k in ("per year", "yearly", "/year", "/yr", "/ year", "per annum", "p.a.")) else ("monthly" if any(k in salary_text for k in ("per month", "monthly", "/month", "/mo", "/ month")) else ("hourly" if any(k in salary_text for k in ("per hour", "hourly", "/hr", "/hour", "/ hour")) else None)))
    # Detect shift type
    raw_shift = str(raw.get("shift_type") or "").lower()
    if raw_shift == "flexible" or "flexible" in (location or "").lower():
        shift_type = "flexible"
    elif any(k in remote_text for k in ("us timezone", "us overlap", "us hours", "est", "pst", "cst", "mst", "eastern time", "pacific time")):
        shift_type = "us_overlap"
    elif any(k in remote_text for k in ("uk timezone", "uk overlap", "gmt", "bst", "ist overlap")):
        shift_type = "uk_overlap"
    elif "night" in remote_text:
        shift_type = "night_shift"
    else:
        shift_type = "flexible"
    return JobRecord(title=title, company=company, description=description, application_url=url, source_name=source_name, external_id=str(raw.get("id")) if raw.get("id") else None, required_skills=list(raw.get("required_skills") or []), experience_requirements=raw.get("experience_requirements"), location=location, country=country or None, remote_eligibility=remote, shift_type=shift_type, work_hours=raw.get("work_hours"), expected_overlap=raw.get("expected_overlap"), salary=salary, salary_classification=salary_classification, currency=currency, frequency=frequency, employment_type=raw.get("employment_type"))


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
