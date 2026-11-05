from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from modules.discovery.base_scraper import JobRecord, normalize_job


def _get_json(url: str, timeout: int = 20) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "AutonomousJobAgent/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class GreenhouseAdapter:
    name = "greenhouse"

    def __init__(self, board_token: str, timeout: int = 20):
        self.board_token, self.timeout = board_token, timeout

    def fetch(self) -> list[JobRecord]:
        data = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{urllib.parse.quote(self.board_token)}/jobs?content=true", self.timeout)
        records = []
        for item in data.get("jobs", []):
            loc = (item.get("location") or {}).get("name")
            desc = item.get("content", "")
            title = item.get("title", "Untitled role")
            rec = normalize_job(
                title=title, company=self.board_token, description=desc,
                application_url=item.get("absolute_url", ""), source_name=self.name,
                external_id=str(item.get("id")), location=loc
            )
            records.append(rec)
        return records


class LeverAdapter:
    name = "lever"

    def __init__(self, company_slug: str, timeout: int = 20):
        self.company_slug, self.timeout = company_slug, timeout

    def fetch(self) -> list[JobRecord]:
        data = _get_json(f"https://api.lever.co/v0/postings/{urllib.parse.quote(self.company_slug)}?mode=json", self.timeout)
        records = []
        for item in data:
            cats = item.get("categories") or {}
            loc = cats.get("location")
            desc = item.get("descriptionPlain") or item.get("description") or ""
            title = item.get("text", "Untitled role")
            rec = normalize_job(
                title=title, company=self.company_slug, description=desc,
                application_url=item.get("hostedUrl", ""), source_name=self.name,
                external_id=str(item.get("id")), location=loc
            )
            if cats.get("commitment"):
                rec.employment_type = cats.get("commitment")
            records.append(rec)
        return records


class AshbyAdapter:
    name = "ashby"

    def __init__(self, board_name: str, timeout: int = 20):
        self.board_name, self.timeout = board_name, timeout

    def fetch(self) -> list[JobRecord]:
        data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{urllib.parse.quote(self.board_name)}", self.timeout)
        records = []
        for item in data.get("jobs", []):
            loc = item.get("location")
            desc = item.get("descriptionPlain", item.get("description", ""))
            title = item.get("title", "Untitled role")
            rec = normalize_job(
                title=title, company=self.board_name, description=desc,
                application_url=item.get("jobUrl", item.get("applyUrl", "")), source_name=self.name,
                external_id=item.get("jobUrl"), location=loc
            )
            if item.get("isRemote"):
                rec.remote_eligibility = "Remote (Worldwide / International)"
            records.append(rec)
        return records
