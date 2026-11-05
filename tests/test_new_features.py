from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models import Base
from database.repositories import (
    get_or_create_candidate_profile,
    save_education,
    save_skill,
    save_experience,
    save_project,
    save_resume,
    save_website,
    save_website_account,
    save_website_form_mapping,
    save_candidate_information_library,
    get_candidate_information_library,
    save_interview,
    get_or_create_user_preferences,
)
from modules.discovery.base_scraper import normalize_job, JobRecord


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_candidate_profile_and_relations(db_session: Session):
    profile = get_or_create_candidate_profile(db_session, "Alice Smith", "alice@example.com")
    assert profile.id is not None
    assert profile.full_name == "Alice Smith"

    edu = save_education(db_session, profile.id, "B.Tech", "Computer Science", "IIT", 2025)
    assert edu.id is not None

    skill = save_skill(db_session, profile.id, "Python", "technical", "expert", 4.5, True)
    assert skill.id is not None

    exp = save_experience(db_session, profile.id, "Software Engineer", "Acme Corp", "2024-01-01", None, "Remote", "Built APIs")
    assert exp.id is not None

    proj = save_project(db_session, profile.id, "Job Scraper", "Autonomous job hunter", None, "Python, SQLite", "2026-01-01", "2026-03-01", True)
    assert proj.id is not None

    resume = save_resume(db_session, profile.id, "/tmp/orig.pdf", "/tmp/parsed.txt", "resume.pdf", "Parsed resume text")
    assert resume.id is not None
    db_session.commit()


def test_website_and_library_management(db_session: Session):
    from database.models import Job
    from database.repositories import upsert_job
    # Create a real job so save_interview FK is satisfied
    job, _ = upsert_job(db_session, {
        "title": "Test Job", "company": "Acme Corp", "description": "Test",
        "application_url": "https://example.com/j/1", "source_name": "test",
        "required_skills": [], "location": "", "remote_eligibility": "india_remote",
    })

    website = save_website(db_session, "Greenhouse", "greenhouse.io", "https://app.greenhouse.io/login")
    assert website.id is not None

    account = save_website_account(db_session, website.id, True, "oauth")
    assert account.id is not None

    mapping = save_website_form_mapping(db_session, website.id, "job_application", '{"name": "full_name"}', "name,email", "phone")
    assert mapping.id is not None

    answer = save_candidate_information_library(
        db_session,
        field_name="years_experience",
        normalized_question="how many years of python experience do you have",
        exact_answer="4 years",
        data_type="integer",
        category="experience",
        verified=True,
        reuse_permission="unrestricted",
        sensitivity="low",
        source="profile"
    )
    assert answer.id is not None

    fetched = get_candidate_information_library(db_session, "how many years of python experience do you have")
    assert fetched is not None
    assert fetched.exact_answer == "4 years"

    interview = save_interview(db_session, job.id, "Acme Corp", "Software Engineer", "technical", '["Q1"]', '["HR1"]', '{}', '{}')
    assert interview.id is not None

    prefs = get_or_create_user_preferences(db_session)
    assert prefs.id is not None
    db_session.commit()


def test_international_job_normalization():
    record = normalize_job({
        "title": "Senior Worldwide Remote Engineer",
        "company": "Global Tech",
        "description": "Work from anywhere in the world. US timezone overlap required. Salary $120,000 / year.",
        "job_url": "https://example.com/job/1",
        "location": "Worldwide",
        "salary": "$120,000 / year",
    }, "global_source")

    assert record.remote_eligibility == "worldwide_remote"
    assert record.shift_type == "us_overlap"
    assert record.salary_classification == "paid_disclosed"
    assert record.currency == "USD"
    assert record.frequency == "yearly"
    assert record.salary == "$120,000 / year"
