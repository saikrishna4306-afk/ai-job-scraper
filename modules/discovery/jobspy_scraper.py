from __future__ import annotations

from modules.discovery.base_scraper import JobRecord


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
            records.append(JobRecord(title=str(item.get("title", "")), company=str(item.get("company", "")), description=str(item.get("description", "")), application_url=str(item.get("job_url", "")), source_name=str(item.get("site", "jobspy")), external_id=str(item.get("job_url") or ""), location=str(item.get("location", "")), remote_eligibility="remote" if "remote" in str(item).lower() else "not specified", salary=str(item.get("min_amount") or "") or None))
        return records
