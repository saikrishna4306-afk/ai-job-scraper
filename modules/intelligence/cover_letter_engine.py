from __future__ import annotations

from pathlib import Path

from modules.discovery.base_scraper import JobRecord
from modules.intelligence.schemas import Profile


class CoverLetterEngine:
    def generate_text(self, job: JobRecord, profile: Profile, matching_skills: list[str] | None = None) -> str:
        skills = matching_skills or profile.technical_skills[:5]
        project = profile.projects[0].get("name", "a relevant project") if profile.projects else "relevant projects"
        return f"Dear Hiring Team,\n\nI am applying for the {job.title} position at {job.company}. My background includes {', '.join(skills) or 'the skills listed in my verified profile'}, and I would welcome the opportunity to apply that experience to your team.\n\nA project I would be glad to discuss is {project}. I have attached my tailored resume for context and would appreciate your consideration.\n\nRegards,\n{profile.full_name or 'Candidate'}\n{profile.email}".strip()

    def generate(self, job: JobRecord, profile: Profile, output_dir: str | Path = "storage/cover_letters", matching_skills: list[str] | None = None) -> tuple[Path, Path]:
        output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{job.company}_{job.title}".replace(" ", "_")
        text = self.generate_text(job, profile, matching_skills)
        docx_path = output_dir / f"{stem}.docx"
        pdf_path = output_dir / f"{stem}.pdf"
        from modules.documents.cover_letter_pdf import write_cover_letter_pdf
        write_cover_letter_pdf(text, pdf_path)
        try:
            from docx import Document
            document = Document(); document.add_paragraph(text); document.save(docx_path)
        except ImportError:
            docx_path.write_text(text, encoding="utf-8")
        return pdf_path, docx_path
