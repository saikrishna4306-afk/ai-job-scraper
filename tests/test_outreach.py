from modules.discovery.base_scraper import JobRecord
from modules.intelligence.schemas import Profile
from modules.recruiters.cold_email_generator import ColdEmailGenerator
from modules.recruiters.recruiter_finder import PublicContact


def test_outreach_draft_mentions_exact_role_and_company():
    draft = ColdEmailGenerator().generate(JobRecord("Backend Developer", "Acme", "Python", "https://example.test", "test", external_id="abc"), Profile(full_name="Candidate", email="a@example.com"), PublicContact("Taylor", "taylor@example.com", "engineer", "https://source.test", "verified"), "referral")
    assert "Backend Developer" in draft.body
    assert "Acme" in draft.body
    assert "Referral request" in draft.subject
