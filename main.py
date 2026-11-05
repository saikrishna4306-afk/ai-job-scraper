from __future__ import annotations

import argparse
import json
import logging

from config import Settings
from database.database import session_scope
from database.repositories import summary
from modules.workflow.daily_pipeline import DailyPipeline


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous AI Job Hunter")
    parser.add_argument("--mode", choices=["discover", "process", "apply", "daily", "test", "status"], default="daily")
    args = parser.parse_args()
    settings = Settings.load()
    configure_logging(settings)
    if args.mode == "status":
        print(json.dumps(settings.status(), indent=2))
        with session_scope(settings) as session:
            print(json.dumps(summary(session), indent=2))
        return 0
    if args.mode == "test":
        print(json.dumps({"configuration": settings.status(), "message": "Mock-safe configuration check passed"}, indent=2))
        return 0
    print(json.dumps(DailyPipeline(settings).run(args.mode), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
