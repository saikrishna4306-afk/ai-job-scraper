from __future__ import annotations

import re
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class CompanyResearch:
    company: str
    website: str | None
    careers_url: str | None
    public_emails: list[str]
    source_urls: list[str]


class CompanyResearcher:
    def research(self, company: str, website: str | None = None) -> CompanyResearch:
        if not website:
            return CompanyResearch(company, None, None, [], [])
        request = urllib.request.Request(website, headers={"User-Agent": "AutonomousJobAgent/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                html = response.read().decode("utf-8", errors="replace")
        except Exception:
            return CompanyResearch(company, website, None, [], [])
        emails = sorted(set(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", html)))
        careers = None
        for href in re.findall(r'href=["\']([^"\']+)["\']', html, re.I):
            if any(token in href.lower() for token in ("career", "job", "work-with-us")):
                careers = urljoin(website, href); break
        return CompanyResearch(company, website, careers, emails, [website])
