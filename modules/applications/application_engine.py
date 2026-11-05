from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from config import Settings
from database.models import Application, ApplicationStatus, Job
from database.repositories import get_or_create_application, transition_application
from modules.applications.answer_manager import AnswerManager, QuestionRequest, classify_question
from modules.applications.field_mapper import FieldMapper
from modules.applications.form_detector import FormDetector
from modules.intelligence.schemas import Profile

logger = logging.getLogger(__name__)


@dataclass
class ApplicationResult:
    status: str
    message: str
    confirmation: dict[str, str] | None = None


class ApplicationEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()
        self.detector, self.mapper, self.answers = FormDetector(), FieldMapper(), AnswerManager()

    def prepare(self, session: Session, job: Job, profile: Profile, resume_path: str | None, cover_letter_path: str | None) -> ApplicationResult:
        application = get_or_create_application(session, job.id)
        application.tailored_resume_path, application.cover_letter_path = resume_path, cover_letter_path
        transition_application(session, application, ApplicationStatus.RESUME_READY, "Documents attached; ready for assisted browser fill")
        if self.settings.require_approval or not self.settings.auto_apply_enabled:
            transition_application(session, application, ApplicationStatus.PENDING_APPROVAL, "Final submission requires explicit approval")
            return ApplicationResult(ApplicationStatus.PENDING_APPROVAL.value, "Prepared and waiting for approval")
        transition_application(session, application, ApplicationStatus.READY_TO_SUBMIT, "Authorized automation enabled")
        return ApplicationResult(ApplicationStatus.READY_TO_SUBMIT.value, "Eligible for supported browser submission")

    def handle_unknown_question(self, session: Session, application: Application, question: str, input_type: str, options: list[str]) -> ApplicationResult:
        request = QuestionRequest(question, input_type, options, classify_question(question))
        answer = self.answers.resolve(session, request)
        if answer is not None:
            return ApplicationResult("ANSWERED", "Verified reusable answer found")
        transition_application(session, application, ApplicationStatus.NEEDS_USER_INPUT, f"Unresolved {request.category} question: {question}")
        return ApplicationResult(ApplicationStatus.NEEDS_USER_INPUT.value, "User input required; application paused")

    def record_confirmation(self, session: Session, application: Application, evidence: dict[str, str]) -> ApplicationResult:
        if not evidence or not evidence.get("evidence"):
            transition_application(session, application, ApplicationStatus.FAILED, "No confirmation evidence")
            return ApplicationResult(ApplicationStatus.FAILED.value, "Submission could not be verified")
        application.confirmation_evidence = evidence["evidence"]; application.submitted_at = datetime.now(timezone.utc)
        transition_application(session, application, ApplicationStatus.CONFIRMATION_VERIFIED, "Portal confirmation evidence captured")
        return ApplicationResult(ApplicationStatus.CONFIRMATION_VERIFIED.value, "Confirmation verified", evidence)
