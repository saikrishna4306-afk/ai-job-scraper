from modules.discovery.base_scraper import JobRecord, deduplicate_jobs, normalize_job


def test_normalization_and_duplicate_detection():
    raw = {"title": "Python Developer", "company": "Acme", "description": "Remote Python role", "url": "https://example.test/job/1"}
    first = normalize_job(raw, "test")
    second = normalize_job(raw, "test")
    assert first.remote_eligibility == "remote"
    assert len(deduplicate_jobs([first, second])) == 1
