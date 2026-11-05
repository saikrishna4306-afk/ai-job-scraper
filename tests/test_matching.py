from modules.discovery.base_scraper import JobRecord
from modules.intelligence.job_matcher import heuristic_match
from modules.intelligence.schemas import Profile


def test_match_never_applies_unverified_profile():
    profile = Profile(verified=False, technical_skills=["Python"])
    job = JobRecord("Python Developer", "Acme", "Remote Python job", "https://example.test", "test")
    result = heuristic_match(job, profile)
    assert result.match_score <= 6
    assert result.should_apply is False
