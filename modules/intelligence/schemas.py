from __future__ import annotations

from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    match_score: int = Field(ge=1, le=10)
    should_apply: bool
    job_level: str = "Unknown"
    remote_eligibility: str = "Unknown"
    shift_type: str = "Unknown"
    work_hours: str = ""
    expected_overlap: str = ""
    salary: str = ""
    salary_classification: str = "Unknown"
    currency: str = "USD"
    frequency: str = "yearly"
    employment_type: str = "Unknown"
    matching_skills: list[str] = []
    missing_skills: list[str] = []
    experience_match: str = ""
    strengths: list[str] = []
    concerns: list[str] = []
    reasoning: str = ""
    recommended_resume_focus: list[str] = []


class Profile(BaseModel):
    verified: bool = False
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    education: list[dict] = []
    degree: str = ""
    college: str = ""
    graduation_year: int | None = None
    technical_skills: list[str] = []
    programming_languages: list[str] = []
    frameworks: list[str] = []
    databases: list[str] = []
    cloud_technologies: list[str] = []
    ai_ml_skills: list[str] = []
    projects: list[dict] = []
    internships: list[dict] = []
    work_experience: list[dict] = []
    certifications: list[str] = []
    achievements: list[str] = []
    languages: list[str] = []
    authorized_application_answers: dict[str, str] = {}
    original_resume_path: str = ""


class OutreachDraft(BaseModel):
    recipient_name: str = ""
    recipient_email: str = ""
    contact_role: str
    subject: str
    body: str
    verification_status: str = "unverified"
