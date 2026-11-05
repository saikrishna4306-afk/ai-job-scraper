from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select

from config import Settings
from database.database import session_scope
from database.models import Job, PipelineRun
from database.repositories import save_document, save_match, summary
from modules.applications.application_engine import ApplicationEngine
from modules.discovery.job_manager import JobManager, load_custom_sources
from modules.discovery.public_ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter
from modules.discovery.jobspy_scraper import JobSpyAdapter
from modules.discovery.rss_scraper import RSSAdapter
from modules.discovery.base_scraper import JobRecord
from modules.intelligence.cover_letter_engine import CoverLetterEngine
from modules.intelligence.interview_generator import InterviewGenerator
from modules.intelligence.job_matcher import JobMatcher
from modules.intelligence.resume_engine import ResumeEngine, load_profile
from modules.notifications.notification_manager import NotificationManager
from modules.notifications.telegram_bot import TelegramBot
from modules.recruiters.cold_email_generator import ColdEmailGenerator
from modules.recruiters.recruiter_finder import PublicContact, RecruiterFinder
from modules.recruiters.company_researcher import CompanyResearcher

logger = logging.getLogger(__name__)


def _adapters(settings: Settings) -> list:
    adapters = [RSSAdapter("remoteok", "https://remoteok.com/remote-jobs.rss"), RSSAdapter("weworkremotely", "https://weworkremotely.com/remote-jobs.rss")]
    jobspy_path = Path("jobspy_sources.json")
    if jobspy_path.exists():
        for item in json.loads(jobspy_path.read_text(encoding="utf-8")):
            if item.get("enabled", True) and item.get("search_term"):
                adapters.append(JobSpyAdapter(item["search_term"], item.get("location", ""), item.get("sites"), min(int(item.get("results_wanted", settings.max_jobs_per_platform)), settings.max_jobs_per_platform)))
    config_path = Path("ats_sources.json")
    if config_path.exists():
        for item in json.loads(config_path.read_text(encoding="utf-8")):
            if item.get("type") == "greenhouse": adapters.append(GreenhouseAdapter(item["board_token"]))
            elif item.get("type") == "lever": adapters.append(LeverAdapter(item["company_slug"]))
            elif item.get("type") == "ashby": adapters.append(AshbyAdapter(item["board_name"]))
    adapters.extend(load_custom_sources())
    return adapters


def _job_record(job: Job) -> JobRecord:
    required = json.loads(job.required_skills_json or "[]") if job.required_skills_json and job.required_skills_json.startswith("[") else []
    return JobRecord(
        title=job.title, company=job.company, description=job.description, application_url=job.application_url,
        source_name=job.source_name, external_id=job.external_id, required_skills=required, location=job.location,
        country=job.country, remote_eligibility=job.remote_eligibility, shift_type=job.shift_type,
        work_hours=job.work_hours, expected_overlap=job.expected_overlap, salary=job.salary,
        salary_classification=job.salary_classification, currency=job.currency, frequency=job.frequency,
        employment_type=job.employment_type, experience_requirements=job.experience_requirements
    )


class DailyPipeline:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()

    def run(self, mode: str = "daily") -> dict:
        with session_scope(self.settings) as session:
            pipeline = PipelineRun(mode=mode); session.add(pipeline); session.flush()
            result = {"discovered": 0, "new_jobs": 0, "relevant": 0, "resumes": 0, "cover_letters": 0, "applications_pending": 0, "outreach_drafts": 0, "interview_packs": 0, "scraper_failures": {}}
            try:
                if mode in {"daily", "discover"}:
                    discovery = JobManager(_adapters(self.settings)).discover(session)
                    result["discovered"], result["new_jobs"], result["scraper_failures"] = len(discovery.jobs), discovery.created_count, discovery.failures
                    description_dir = Path("storage/job_descriptions")
                    description_dir.mkdir(parents=True, exist_ok=True)
                    for record in discovery.jobs:
                        safe_name = f"{record.company}_{record.title}".replace("/", "_").replace(" ", "_")
                        (description_dir / f"{safe_name}.txt").write_text(record.description, encoding="utf-8")
                if mode in {"daily", "process", "apply"}:
                    profile = load_profile()
                    matcher = JobMatcher(minimum_score=self.settings.minimum_match_score)
                    resume_engine, cover_engine, interview = ResumeEngine(), CoverLetterEngine(), InterviewGenerator()
                    app_engine = ApplicationEngine(self.settings)
                    for job in session.scalars(select(Job).where(Job.processing_status != "SKIPPED")):
                        matched = matcher.match(_job_record(job), profile)
                        save_match(session, job, matched.model_dump())
                        if not matched.should_apply: continue
                        result["relevant"] += 1
                        content, resume_path = resume_engine.generate(_job_record(job), profile, matched.recommended_resume_focus)
                        cover_pdf, _ = cover_engine.generate(_job_record(job), profile, matching_skills=matched.matching_skills)
                        save_document(session, job.id, "tailored_resume", str(resume_path)); save_document(session, job.id, "cover_letter", str(cover_pdf))
                        result["resumes"] += 1; result["cover_letters"] += 1
                        if mode in {"daily", "apply"}:
                            application = app_engine.prepare(session, job, profile, str(resume_path), str(cover_pdf))
                            if application.status == "PENDING_APPROVAL": result["applications_pending"] += 1
                        interview_path = interview.generate(_job_record(job), profile)
                        import shutil
                        pack_dir = interview_path.parent
                        shutil.copyfile(resume_path, pack_dir / Path(resume_path).name)
                        shutil.copyfile(cover_pdf, pack_dir / Path(cover_pdf).name)
                        result["interview_packs"] += 1
                        result["outreach_drafts"] += self._outreach(session, job, profile, str(resume_path))
                result["database"] = summary(session)
                pipeline.status, pipeline.summary_json = "SUCCEEDED", json.dumps(result)
            except Exception as exc:
                pipeline.status, pipeline.error_info = "FAILED", str(exc); logger.exception("daily pipeline failed")
                raise
            finally:
                from database.models import utcnow
                pipeline.finished_at = utcnow()
            notifier = NotificationManager(TelegramBot(self.settings))
            notifier.enqueue(session, "daily_summary", {"text": notifier.daily_summary(result.get("database", {}), result.get("scraper_failures"))})
            return result

    def _outreach(self, session, job: Job, profile, resume_path: str) -> int:
        """Create drafts only for contacts explicitly supplied in public_contacts.json."""
        path = Path("public_contacts.json")
        if not path.exists(): return 0
        entries = json.loads(path.read_text(encoding="utf-8"))
        contacts = [item for item in entries if item.get("company", "").lower() == job.company.lower()]
        generator, created = ColdEmailGenerator(), 0
        from database.repositories import save_outreach
        for raw in contacts:
            contact = PublicContact(raw.get("name", ""), raw.get("email"), raw.get("role", "recruiter"), raw.get("source_url", ""), raw.get("verification_status", "unverified"))
            purpose = raw.get("purpose", "recruiter")
            draft = generator.generate(_job_record(job), profile, contact, purpose)
            save_outreach(session, job_id=job.id, recipient_name=draft.recipient_name, recipient_email=draft.recipient_email or None, company=job.company, job_title=job.title, contact_role=purpose, contact_source=contact.source_url, verification_status=draft.verification_status, subject=draft.subject, body=draft.body, attachment_path=resume_path)
            safe = f"{job.company}_{purpose}_{contact.name or 'contact'}".replace(" ", "_")
            Path("storage/recruiter_emails").mkdir(parents=True, exist_ok=True); Path("storage/recruiter_emails", safe + ".txt").write_text(f"Subject: {draft.subject}\n\n{draft.body}", encoding="utf-8")
            created += 1
        return created
