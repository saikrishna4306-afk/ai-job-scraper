from __future__ import annotations

from modules.discovery.base_scraper import JobRecord
from modules.intelligence.schemas import OutreachDraft, Profile
from modules.recruiters.recruiter_finder import PublicContact


class ColdEmailGenerator:
    def generate(self, job: JobRecord, profile: Profile, contact: PublicContact, purpose: str = "recruiter") -> OutreachDraft:
        first_name = contact.name.split()[0] if contact.name else "there"
        skills = ", ".join(profile.technical_skills[:5]) or "the skills in my verified profile"
        project = profile.projects[0].get("name", "a relevant project") if profile.projects else "a relevant project"
        if purpose == "referral":
            subject = f"Referral request — {job.title} ({job.external_id or 'job opening'})"
            ask = f"Would you be comfortable referring me, if you feel my background is a fit?"
        elif purpose == "hiring_manager":
            subject = f"Interest in {job.title} at {job.company}"
            ask = "I would appreciate any guidance on the team and application process."
        else:
            subject = f"Application for {job.title} at {job.company}"
            ask = "I would be grateful if you could point me to the appropriate next step."
        body = f"Hi {first_name},\n\nI am reaching out about the {job.title} role at {job.company}. My background includes {skills}, and I built {project}.\n\n{ask} I have attached my tailored resume and included my portfolio below.\n\nJob: {job.application_url}\nPortfolio: {profile.github_url or profile.portfolio_url or 'available on request'}\n\nThank you,\n{profile.full_name or 'Candidate'}\n{profile.email}"
        return OutreachDraft(recipient_name=contact.name, recipient_email=contact.email or "", contact_role=purpose, subject=subject, body=body, verification_status=contact.verification_status)
