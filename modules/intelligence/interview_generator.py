from __future__ import annotations

from pathlib import Path

from modules.discovery.base_scraper import JobRecord
from modules.intelligence.schemas import Profile


class InterviewGenerator:
    def generate(self, job: JobRecord, profile: Profile, output_dir: str | Path = "storage/interview_prep") -> Path:
        folder = Path(output_dir) / f"{job.company}_{job.title}".replace("/", "_")
        folder.mkdir(parents=True, exist_ok=True)
        skills = ", ".join(profile.technical_skills + profile.frameworks + profile.databases)
        text = f"# Interview preparation: {job.title} at {job.company}\n\n## Job summary\n{job.description[:2500]}\n\n## Technical focus\n{skills or 'Complete the verified profile to personalize this section.'}\n\n## Questions\n- Which part of the role's technical responsibilities best matches your projects?\n- Walk through a project where you used the listed technologies.\n- How would you test and monitor a service for this role?\n- What tradeoffs would you discuss with the team?\n\n## Candidate questions\n- What would success look like in the first 90 days?\n- How does the team review and deploy changes?\n"
        md = folder / "interview_preparation.md"; md.write_text(text, encoding="utf-8")
        from modules.documents.interview_pdf import write_interview_pdf
        write_interview_pdf(text, folder / "interview_preparation.pdf")
        (folder / "job_description.txt").write_text(job.description, encoding="utf-8")
        return md
