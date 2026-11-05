from __future__ import annotations

import json
import urllib.request
from typing import Any

from modules.discovery.base_scraper import JobRecord, normalize_job
from modules.discovery.rss_scraper import RSSAdapter


class CustomWebsiteAdapter:
    def __init__(self, name: str, url: str, method: str = "json", rss_url: str | None = None):
        self.name, self.url, self.method, self.rss_url = name, url, method, rss_url

    def fetch(self) -> list[JobRecord]:
        if self.method == "rss" and self.rss_url:
            return RSSAdapter(self.name, self.rss_url).fetch()
        request = urllib.request.Request(self.url, headers={"User-Agent": "AutonomousJobAgent/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
        if self.method == "json":
            payload: Any = json.loads(raw)
            items = payload if isinstance(payload, list) else payload.get("jobs", payload.get("results", []))
            return [normalize_job(item, self.name) for item in items if isinstance(item, dict)]
        raise ValueError("HTML custom extraction requires a permitted selector adapter; use RSS or structured JSON")
