from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Iterable

from sqlalchemy.orm import Session

from database.repositories import upsert_job
from modules.discovery.base_scraper import JobRecord, SourceAdapter, deduplicate_jobs

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryResult:
    jobs: list[JobRecord] = field(default_factory=list)
    created_count: int = 0
    failures: dict[str, str] = field(default_factory=dict)


class JobManager:
    def __init__(self, adapters: Iterable[SourceAdapter]):
        self.adapters = list(adapters)

    def discover(self, session: Session) -> DiscoveryResult:
        result = DiscoveryResult()
        for adapter in self.adapters:
            try:
                fetched = deduplicate_jobs(adapter.fetch())
                for record in fetched:
                    job, created = upsert_job(session, record.as_dict())
                    if created:
                        result.created_count += 1
                    result.jobs.append(record)
            except Exception as exc:  # one source must not stop the run
                logger.exception("discovery source failed", extra={"source": getattr(adapter, "name", type(adapter).__name__)})
                result.failures[getattr(adapter, "name", type(adapter).__name__)] = str(exc)
        return result


def load_custom_sources(path: str = "custom_sources.json") -> list[SourceAdapter]:
    try:
        sources = json.loads(open(path, encoding="utf-8").read())
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    from modules.discovery.custom_website_scraper import CustomWebsiteAdapter
    return [CustomWebsiteAdapter(item["name"], item["url"], item.get("method", "json"), item.get("rss_url")) for item in sources if item.get("enabled", True) and item.get("url")]
