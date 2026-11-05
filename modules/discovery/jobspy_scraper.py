from __future__ import annotations

from modules.discovery.base_scraper import JobRecord, normalize_job


class JobSpyAdapter:
    """Optional JobSpy integration; it is isolated because supported sites change."""

    def __init__(self, search_term: str, location: str = "", sites: list[str] | None = None, results_wanted: int = 20):
        self.search_term, self.location, self.sites, self.results_wanted = search_term, location, sites or ["linkedin", "indeed", "glassdoor", "zip_recruiter"], results_wanted
        self.name = "jobspy"

    def fetch(self) -> list[JobRecord]:
        try:
            from jobspy import scrape_jobs
        except ImportError as exc:
            raise RuntimeError("JobSpy is not installed; enable it from requirements.txt") from exc
        frame = scrape_jobs(site_name=self.sites, search_term=self.search_term, location=self.location, results_wanted=self.results_wanted, country_indeed="India")
        records: list[JobRecord] = []
        for item in frame.to_dict("records"):
            records.append(normalize_job(item, str(item.get("site", "jobspy"))))
        return records
