from __future__ import annotations

import re
from dataclasses import dataclass

from modules.recruiters.company_researcher import CompanyResearch


@dataclass
class PublicContact:
    name: str
    email: str | None
    role: str
    source_url: str
    verification_status: str = "unverified"


class RecruiterFinder:
    """Only records contacts the user supplies or that are explicitly public on a source page."""

    def find(self, research: CompanyResearch, supplied_contacts: list[dict] | None = None) -> list[PublicContact]:
        contacts = []
        for raw in supplied_contacts or []:
            email = raw.get("email")
            if email and not re.fullmatch(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", email):
                email = None
            contacts.append(PublicContact(name=raw.get("name", ""), email=email, role=raw.get("role", "recruiter"), source_url=raw.get("source_url", ""), verification_status="verified" if raw.get("verified") and email else "unverified"))
        for email in research.public_emails:
            contacts.append(PublicContact(name="", email=email, role="public contact", source_url=research.website or "", verification_status="public-unverified"))
        return contacts
