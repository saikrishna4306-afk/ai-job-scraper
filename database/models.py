from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class ApplicationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    MATCHED = "MATCHED"
    RESUME_READY = "RESUME_READY"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    READY_TO_SUBMIT = "READY_TO_SUBMIT"
    SUBMITTED = "SUBMITTED"
    CONFIRMATION_VERIFIED = "CONFIRMATION_VERIFIED"
    FAILED = "FAILED"
    NEEDS_USER_INPUT = "NEEDS_USER_INPUT"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    SKIPPED = "SKIPPED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class EmploymentType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    CONTRACTOR = "contractor"
    STUDENT = "student"


class RemoteEligibility(str, Enum):
    NOT_REMOTE = "not_remote"
    INDIA_REMOTE = "india_remote"
    WORLDWIDE_REMOTE = "worldwide_remote"
    HYBRID_INDIA = "hybrid_india"
    HYBRID_OTHER = "hybrid_other"
    HYBRID_ONSITE_INDIA = "hybrid_onsite_india"
    HYBRID_ONSITE_OTHER = "hybrid_onsite_other"
    RELOCATION_REQUIRED = "relocation_required"
    INELIGIBLE = "ineligible"


class CompensationClassification(str, Enum):
    UNPAID = "unpaid"
    PAID_DISCLOSED = "paid_disclosed"
    PAID_CONFIRMED = "paid_confirmed"
    COMPENSATION_UNCLEAR = "compensation_unclear"


class ShiftType(str, Enum):
    FIXED = "fixed"
    ROTATIONAL = "rotational"
    NIGHT_SHIFT = "night_shift"
    OVERLAP_SUPPORTED = "overlap_supported"
    FLEXIBLE = "flexible"


class JobSource(Base):
    __tablename__ = "job_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    source_type: Mapped[str] = mapped_column(String(40), default="adapter")
    base_url: Mapped[str | None] = mapped_column(String(500))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_job_dedupe_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(255))
    dedupe_key: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(300))
    company: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    required_skills_json: Mapped[str] = mapped_column(Text, default="[]")
    experience_requirements: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(300))
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remote_eligibility: Mapped[RemoteEligibility | None] = mapped_column(String(30), nullable=True)
    shift_type: Mapped[ShiftType | None] = mapped_column(String(30), nullable=True)
    work_hours: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_overlap: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary: Mapped[str | None] = mapped_column(String(200), nullable=True)
    salary_classification: Mapped[CompensationClassification | None] = mapped_column(String(30), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    employment_type: Mapped[EmploymentType | None] = mapped_column(String(40), nullable=True)
    posting_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    application_url: Mapped[str] = mapped_column(String(1000))
    source_name: Mapped[str] = mapped_column(String(120), index=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    processing_status: Mapped[str] = mapped_column(String(50), default="DISCOVERED")
    job_matches: Mapped[list["JobMatch"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    outreach: Mapped[list["OutreachEmail"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    interviews: Mapped[list["Interview"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobMatch(Base):
    __tablename__ = "job_matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True)
    match_score: Mapped[float] = mapped_column(Float)
    should_apply: Mapped[bool] = mapped_column(Boolean, default=False)
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    job: Mapped[Job] = relationship(back_populates="job_matches")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"))
    kind: Mapped[str] = mapped_column(String(40))
    path: Mapped[str] = mapped_column(String(1000))
    version: Mapped[str] = mapped_column(String(80), default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Recruiter(Base):
    __tablename__ = "recruiters"
    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(300), index=True)
    name: Mapped[str | None] = mapped_column(String(250))
    email: Mapped[str | None] = mapped_column(String(320))
    role: Mapped[str] = mapped_column(String(120))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    verification_status: Mapped[str] = mapped_column(String(40), default="unverified")
    notes: Mapped[str | None] = mapped_column(Text)


class OutreachEmail(Base):
    __tablename__ = "outreach_emails"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    recruiter_id: Mapped[int | None] = mapped_column(ForeignKey("recruiters.id"))
    recipient_name: Mapped[str | None] = mapped_column(String(250))
    recipient_email: Mapped[str | None] = mapped_column(String(320))
    company: Mapped[str] = mapped_column(String(300))
    job_title: Mapped[str] = mapped_column(String(300))
    contact_role: Mapped[str] = mapped_column(String(80))
    contact_source: Mapped[str | None] = mapped_column(String(1000))
    verification_status: Mapped[str] = mapped_column(String(40), default="unverified")
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    attachment_path: Mapped[str | None] = mapped_column(String(1000))
    sending_status: Mapped[str] = mapped_column(String(40), default="DRAFT")
    follow_up_status: Mapped[str] = mapped_column(String(40), default="NOT_DUE")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    job: Mapped[Job] = relationship(back_populates="outreach")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", name="uq_application_job"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    tailored_resume_path: Mapped[str | None] = mapped_column(String(1000))
    cover_letter_path: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(40), default=ApplicationStatus.DISCOVERED.value)
    approval_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmation_id: Mapped[str | None] = mapped_column(String(255))
    confirmation_evidence: Mapped[str | None] = mapped_column(Text)
    error_info: Mapped[str | None] = mapped_column(Text)
    job: Mapped[Job] = relationship(back_populates="applications")
    events: Mapped[list["ApplicationEvent"]] = relationship(cascade="all, delete-orphan")


class ApplicationQuestion(Base):
    __tablename__ = "application_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    input_type: Mapped[str] = mapped_column(String(40))
    options_json: Mapped[str] = mapped_column(Text, default="[]")
    category: Mapped[str] = mapped_column(String(40), default="general")
    answer: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")


class AnswerVault(Base):
    __tablename__ = "answer_vault"
    id: Mapped[int] = mapped_column(primary_key=True)
    normalized_question: Mapped[str] = mapped_column(String(500), unique=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40), default="general")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(50))
    payload_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    error_info: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="RUNNING")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    error_info: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApplicationEvent(Base):
    __tablename__ = "application_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(200))
    job_authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    educations: Mapped[list["Education"]] = relationship(back_populates="candidate_profile", cascade="all, delete-orphan")
    skills: Mapped[list["Skill"]] = relationship(back_populates="candidate_profile", cascade="all, delete-orphan")
    experiences: Mapped[list["Experience"]] = relationship(back_populates="candidate_profile", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="candidate_profile", cascade="all, delete-orphan")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="candidate_profile", cascade="all, delete-orphan", foreign_keys="Resume.candidate_profile_id")


class Education(Base):
    __tablename__ = "educations"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"))
    degree: Mapped[str] = mapped_column(String(150))
    field_of_study: Mapped[str] = mapped_column(String(150))
    institution: Mapped[str] = mapped_column(String(300))
    graduation_year: Mapped[int]
    gpa: Mapped[str | None] = mapped_column(String(20))
    start_year: Mapped[int | None] = mapped_column(Integer)
    activities: Mapped[str | None] = mapped_column(Text)
    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="educations")


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="technical")
    proficiency: Mapped[str | None] = mapped_column(String(30))
    years_experience: Mapped[float | None] = mapped_column(Float)
    is_core: Mapped[bool] = mapped_column(Boolean, default=True)
    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="skills")


class Experience(Base):
    __tablename__ = "experiences"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"))
    title: Mapped[str] = mapped_column(String(150))
    company: Mapped[str] = mapped_column(String(300))
    start_date: Mapped[str] = mapped_column(String(50))
    end_date: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    is_internship: Mapped[bool] = mapped_column(Boolean, default=False)
    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="experiences")


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500))
    technologies: Mapped[str] = mapped_column(Text, default="[]")
    start_date: Mapped[str] = mapped_column(String(50))
    end_date: Mapped[str | None] = mapped_column(String(50))
    is_major: Mapped[bool] = mapped_column(Boolean, default=False)
    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="projects")


class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"))
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)
    parsed_path: Mapped[str | None] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(200))
    parsed_text: Mapped[Text | None] = mapped_column(Text)
    parse_status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="resumes", foreign_keys="Resume.candidate_profile_id")


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    linkedin_url: Mapped[str] = mapped_column(String(500), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(200))
    team: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(300))
    source: Mapped[str] = mapped_column(String(100))
    referral_eligible: Mapped[bool] = mapped_column(Boolean, default=True)


class UserPreferences(Base):
    """User preferences for job discovery, matching, outreach, etc."""
    __tablename__ = "user_preferences"
    id: Mapped[int] = mapped_column(primary_key=True)
    auto_apply: Mapped[str | None] = mapped_column(String(40), default="disabled")
    preferred_remoteness: Mapped[str] = mapped_column(String(30), default="any")
    focus_roles: Mapped[str] = mapped_column(Text, default="[]")
    prefer_paid_only: Mapped[bool] = mapped_column(Boolean, default=False)
    night_owl: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_interval_days: Mapped[int] = mapped_column(Integer, default=7)
    min_match_score: Mapped[float] = mapped_column(Float, default=7.0)


class Interview(Base):
    """Job-specific interview preparation documents."""
    __tablename__ = "interviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    company: Mapped[str] = mapped_column(String(300), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    preparation_type: Mapped[str] = mapped_column(String(40), default="standard")
    technical_questions_json: Mapped[str] = mapped_column(Text, default="{}")
    hr_questions_json: Mapped[str] = mapped_column(Text, default="{}")
    project_specific_questions_json: Mapped[str] = mapped_column(Text, default="{}")
    suggested_answers_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    job: Mapped["Job"] = relationship(back_populates="interviews")


class Website(Base):
    """Registry of discovered job websites (Part 4)."""
    __tablename__ = "websites"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    domain: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    login_url: Mapped[str | None] = mapped_column(String(500))
    account_status: Mapped[str] = mapped_column(String(40), default="disconnected")
    authentication_method: Mapped[str] = mapped_column(String(40), default="manual")
    connection_status: Mapped[str] = mapped_column(String(30), default="never_connected")
    last_successful_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session_valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supported_automation: Mapped[str] = mapped_column(String(50), default="limited")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class WebsiteAccount(Base):
    """Individual authenticated user account on a website."""
    __tablename__ = "website_accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"))
    mfa_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    login_success_count: Mapped[int] = mapped_column(Integer, default=0)
    login_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    connection_source: Mapped[str] = mapped_column(String(40), default="manual")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class WebsiteFormMapping(Base):
    """Reusable form field mapping for a website."""
    __tablename__ = "website_form_mappings"
    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"))
    form_name: Mapped[str] = mapped_column(String(100))
    field_mapping_json: Mapped[str] = mapped_column(Text, default="{}")
    required_fields: Mapped[str] = mapped_column(Text, default="[]")
    optional_fields: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CandidateInformationLibrary(Base):
    """Approved answers for reusable application questions (Part 13)."""
    __tablename__ = "candidate_information_library"
    id: Mapped[int] = mapped_column(primary_key=True)
    field_name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_question: Mapped[str] = mapped_column(String(500), unique=True)
    exact_answer: Mapped[str] = mapped_column(Text, nullable=False)
    data_type: Mapped[str] = mapped_column(String(40), default="text")
    category: Mapped[str] = mapped_column(String(40), default="general")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    reuse_permission: Mapped[str] = mapped_column(String(40), default="any")
    sensitivity: Mapped[str] = mapped_column(String(30), default="none")
    source: Mapped[str] = mapped_column(String(100))
    date_collected: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
