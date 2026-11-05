from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models import Application, ApplicationEvent, ApplicationStatus, CandidateInformationLibrary, CandidateProfile, Document, Education, Employee, Experience, Interview, Job, JobMatch, OutreachEmail, Project, Recruiter, Resume, Skill, UserPreferences, Website, WebsiteAccount, WebsiteFormMapping


def dedupe_key(external_id: str | None, url: str, company: str, title: str, description: str) -> str:
    normalized_url = url.strip().lower().split("#", 1)[0].rstrip("/")
    clean_description = re.sub(r"\W+", " ", description.lower())[:2000]
    payload = "|".join([external_id or "", normalized_url, company.lower().strip(), title.lower().strip(), clean_description])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def upsert_job(session: Session, data: dict[str, Any]) -> tuple[Job, bool]:
    key = data.get("dedupe_key") or dedupe_key(data.get("external_id"), data.get("application_url", ""), data.get("company", ""), data.get("title", ""), data.get("description", ""))
    job = session.scalar(select(Job).where(Job.dedupe_key == key))
    created = job is None
    if job is None:
        job = Job(
            dedupe_key=key,
            title=data["title"],
            company=data["company"],
            description=data.get("description", ""),
            application_url=data.get("application_url", ""),
            source_name=data.get("source_name", "unknown"),
        )
        session.add(job)
    # Always update these fields (new and existing)
    updatable = (
        "external_id", "experience_requirements", "location", "country",
        "remote_eligibility", "shift_type", "work_hours", "expected_overlap",
        "salary", "salary_classification", "currency", "frequency",
        "employment_type", "posting_date", "deadline", "processing_status",
    )
    for field in updatable:
        if field in data and data[field] is not None:
            setattr(job, field, data[field])
    # required_skills_json: accept list or raw JSON string
    if "required_skills" in data and data["required_skills"] is not None:
        job.required_skills_json = json.dumps(data["required_skills"]) if isinstance(data["required_skills"], list) else str(data["required_skills"])
    elif "required_skills_json" in data and data["required_skills_json"] is not None:
        job.required_skills_json = data["required_skills_json"]
    session.flush()
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


def get_or_create_candidate_profile(session: Session, full_name: str, email: str) -> CandidateProfile:
    profile = session.scalar(select(CandidateProfile).where(CandidateProfile.email == email))
    if profile is None:
        profile = CandidateProfile(full_name=full_name, email=email)
        session.add(profile)
        session.flush()
    return profile


def save_education(session: Session, candidate_profile_id: int, degree: str, field_of_study: str, institution: str, graduation_year: int, gpa: str | None = None, start_year: int | None = None, activities: str | None = None) -> Education:
    edu = Education(candidate_profile_id=candidate_profile_id, degree=degree, field_of_study=field_of_study, institution=institution, graduation_year=graduation_year, gpa=gpa, start_year=start_year, activities=activities)
    session.add(edu)
    session.flush()
    return edu


def save_skill(session: Session, candidate_profile_id: int, name: str, category: str = "technical", proficiency: str | None = None, years_experience: float | None = None, is_core: bool = True) -> Skill:
    skill = Skill(candidate_profile_id=candidate_profile_id, name=name, category=category, proficiency=proficiency, years_experience=years_experience, is_core=is_core)
    session.add(skill)
    session.flush()
    return skill


def save_experience(session: Session, candidate_profile_id: int, title: str, company: str, start_date: str, end_date: str | None, location: str | None, description: str, is_internship: bool = False) -> Experience:
    exp = Experience(candidate_profile_id=candidate_profile_id, title=title, company=company, start_date=start_date, end_date=end_date, location=location, description=description, is_internship=is_internship)
    session.add(exp)
    session.flush()
    return exp


def save_project(session: Session, candidate_profile_id: int, name: str, description: str, url: str | None, technologies: str, start_date: str, end_date: str | None, is_major: bool = False) -> Project:
    proj = Project(candidate_profile_id=candidate_profile_id, name=name, description=description, url=url, technologies=technologies, start_date=start_date, end_date=end_date, is_major=is_major)
    session.add(proj)
    session.flush()
    return proj


def save_resume(session: Session, candidate_profile_id: int, original_path: str, parsed_path: str | None, original_filename: str, parsed_text: str | None) -> Resume:
    resume = Resume(candidate_profile_id=candidate_profile_id, original_path=original_path, parsed_path=parsed_path, original_filename=original_filename, parsed_text=parsed_text)
    session.add(resume)
    session.flush()
    return resume


def save_recruiter(session: Session, **data: Any) -> Recruiter:
    recruiter = session.scalar(select(Recruiter).where(Recruiter.source_url == data.get("source_url"))) if data.get("source_url") else None
    if recruiter is None:
        if "role" not in data:
            data["role"] = "recruiter"
        recruiter = Recruiter(**data)
        session.add(recruiter)
    return recruiter


def save_website(session: Session, name: str, domain: str, login_url: str | None = None) -> Website:
    website = session.scalar(select(Website).where(Website.domain == domain))
    if website is None:
        website = Website(name=name, domain=domain, login_url=login_url, account_status="disconnected")
        session.add(website)
        session.flush()
    return website


def save_website_account(session: Session, website_id: int, mfa_verified: bool = False, connection_source: str = "manual") -> WebsiteAccount:
    account = WebsiteAccount(website_id=website_id, mfa_verified=mfa_verified, connection_source=connection_source)
    session.add(account)
    session.flush()
    return account


def save_website_form_mapping(session: Session, website_id: int, form_name: str, field_mapping_json: str, required_fields: str, optional_fields: str) -> WebsiteFormMapping:
    mapping = WebsiteFormMapping(website_id=website_id, form_name=form_name, field_mapping_json=field_mapping_json, required_fields=required_fields, optional_fields=optional_fields)
    session.add(mapping)
    session.flush()
    return mapping


def save_candidate_information_library(session: Session, field_name: str, normalized_question: str, exact_answer: str, data_type: str, category: str, verified: bool, reuse_permission: str, sensitivity: str, source: str, expires_at: str | None = None) -> CandidateInformationLibrary:
    answer = CandidateInformationLibrary(field_name=field_name, normalized_question=normalized_question, exact_answer=exact_answer, data_type=data_type, category=category, verified=verified, reuse_permission=reuse_permission, sensitivity=sensitivity, source=source, expires_at=expires_at and str(expires_at))
    session.add(answer)
    session.flush()
    return answer


def get_candidate_information_library(session: Session, normalized_question: str, reuse_permitted: bool = True) -> CandidateInformationLibrary | None:
    from datetime import datetime, timezone
    answer = session.scalar(select(CandidateInformationLibrary).where(CandidateInformationLibrary.normalized_question == normalized_question))
    if answer is None:
        return None
    if not answer.verified or not reuse_permitted:
        return None
    if answer.expires_at and datetime.fromisoformat(answer.expires_at) < datetime.now(timezone.utc):
        return None
    return answer


def save_interview(session: Session, job_id: int, company: str, role: str, preparation_type: str, technical_questions_json: str = "{}", hr_questions_json: str = "{}", project_specific_questions_json: str = "{}", suggested_answers_json: str = "{}") -> Interview:
    interview = Interview(job_id=job_id, company=company, role=role, preparation_type=preparation_type, technical_questions_json=technical_questions_json, hr_questions_json=hr_questions_json, project_specific_questions_json=project_specific_questions_json, suggested_answers_json=suggested_answers_json)
    session.add(interview)
    session.flush()
    return interview


def get_or_create_user_preferences(session: Session) -> UserPreferences:
    prefs = session.scalar(select(UserPreferences))
    if prefs is None:
        prefs = UserPreferences()
        session.add(prefs)
        session.flush()
    return prefs