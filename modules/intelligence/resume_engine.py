from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from modules.discovery.base_scraper import JobRecord
from modules.intelligence.schemas import Profile


def load_profile(path: str | Path = "master_profile.json") -> Profile:
    return Profile.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))


def extract_resume_text(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        except ImportError as exc:
            raise RuntimeError("pypdf is required for PDF extraction") from exc
    if path.suffix.lower() == ".docx":
        try:
            from docx import Document
            return "\n".join(paragraph.text for paragraph in Document(str(path)).paragraphs)
        except ImportError as exc:
            raise RuntimeError("python-docx is required for DOCX extraction") from exc
    raise ValueError("Only PDF and DOCX resumes are supported")


def propose_profile_from_resume(text: str) -> dict[str, Any]:
    """Conservative extraction: propose only explicit contact and skill tokens."""
    email = next(iter(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)), "")
    phone = next(iter(re.findall(r"(?:\+?\d[\d ()-]{7,}\d)", text)), "")
    known = ["Python", "Django", "FastAPI", "React", "JavaScript", "SQL", "PostgreSQL", "AWS", "Docker", "Git", "LangChain", "FAISS", "Gemini"]
    skills = [skill for skill in known if re.search(r"\b" + re.escape(skill) + r"\b", text, re.I)]
    return {"email": email, "phone": phone, "technical_skills": skills, "_needs_confirmation": True, "_source": "resume extraction proposal"}


class ResumeEngine:
    def __init__(self, storage_dir: str | Path = "storage/resumes"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def tailored_content(self, job: JobRecord, profile: Profile, focus: list[str] | None = None) -> dict[str, Any]:
        focus = focus or profile.technical_skills + profile.frameworks + profile.programming_languages
        relevant_projects = [item for item in profile.projects if any(term.lower() in json.dumps(item).lower() for term in focus)]
        summary = f"{profile.full_name or 'Candidate'} with experience in {', '.join(focus[:6])}. Interested in the {job.title} role at {job.company}.".strip()
        return {"name": profile.full_name, "email": profile.email, "phone": profile.phone, "location": profile.location, "links": [x for x in (profile.linkedin_url, profile.github_url, profile.portfolio_url) if x], "summary": summary, "skills": focus, "projects": relevant_projects or profile.projects, "experience": profile.work_experience + profile.internships, "education": profile.education, "certifications": profile.certifications}

    def generate(self, job: JobRecord, profile: Profile, focus: list[str] | None = None) -> tuple[dict[str, Any], Path]:
        content = self.tailored_content(job, profile, focus)
        safe_company = re.sub(r"[^A-Za-z0-9]+", "_", job.company).strip("_") or "Company"
        safe_role = re.sub(r"[^A-Za-z0-9]+", "_", job.title).strip("_") or "Role"
        path = self.storage_dir / f"{safe_company}_{safe_role}_{job.discovered_at.date().isoformat()}.pdf"
        from modules.documents.resume_pdf import write_resume_pdf
        write_resume_pdf(content, path)
        return content, path
