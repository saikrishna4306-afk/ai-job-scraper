from __future__ import annotations

import re

from modules.discovery.base_scraper import JobRecord


class JobAnalyzer:
    """Deterministic JD analysis used before optional Gemini enrichment."""

    def analyze(self, job: JobRecord) -> dict[str, list[str] | str]:
        vocabulary = ("python", "django", "fastapi", "flask", "react", "javascript", "typescript", "sql", "postgresql", "aws", "docker", "kubernetes", "langchain", "machine learning")
        text = f"{job.title} {job.description}".lower()
        skills = [term for term in vocabulary if re.search(r"\b" + re.escape(term) + r"\b", text)]
        level = "Internship" if "intern" in text else "Entry Level" if "entry" in text or "junior" in text else "Not specified"
        return {"required_skills": skills, "job_level": level, "remote_eligibility": "remote" if "remote" in text else "not specified"}
