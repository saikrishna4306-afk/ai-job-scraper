from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from modules.discovery.base_scraper import JobRecord


class RSSAdapter:
    def __init__(self, name: str, rss_url: str, timeout: int = 20):
        self.name, self.rss_url, self.timeout = name, rss_url, timeout

    def fetch(self) -> list[JobRecord]:
        request = urllib.request.Request(self.rss_url, headers={"User-Agent": "AutonomousJobAgent/1.0"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            root = ET.fromstring(response.read())
        jobs: list[JobRecord] = []
        for item in root.findall(".//item"):
            text = lambda tag: (item.findtext(tag) or "").strip()
            description = re.sub(r"<[^>]+>", " ", text("description")).strip()
            jobs.append(JobRecord(title=text("title") or "Untitled role", company=self.name, description=description, application_url=text("link"), source_name=self.name, external_id=text("guid") or None, location="Remote", remote_eligibility="remote"))
        return jobs
