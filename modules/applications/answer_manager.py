from __future__ import annotations

import re
from dataclasses import dataclass
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import AnswerVault


SENSITIVE_TERMS = ("authorized", "sponsor", "visa", "criminal", "disability", "gender", "salary", "relocat", "citizenship")


def normalize_question(question: str) -> str:
    return re.sub(r"\W+", " ", question.lower()).strip()


def classify_question(question: str) -> str:
    normalized = normalize_question(question)
    if any(term in normalized for term in SENSITIVE_TERMS):
        return "sensitive"
    if any(term in normalized for term in ("legally", "agree", "declar", "consent")):
        return "legal"
    if any(term in normalized for term in ("why", "interest", "describe", "tell us")):
        return "job-specific"
    return "general"


@dataclass
class QuestionRequest:
    question: str
    input_type: str
    options: list[str]
    category: str


class AnswerManager:
    def lookup(self, session: Session, question: str) -> AnswerVault | None:
        return session.scalar(select(AnswerVault).where(AnswerVault.normalized_question == normalize_question(question), AnswerVault.verified.is_(True)))

    def save(self, session: Session, question: str, answer: str, category: str, verified: bool = True) -> AnswerVault:
        normalized = normalize_question(question)
        item = session.scalar(select(AnswerVault).where(AnswerVault.normalized_question == normalized))
        if item is None:
            item = AnswerVault(normalized_question=normalized, question=question, answer=answer, category=category, verified=verified); session.add(item)
        else:
            item.answer, item.category, item.verified = answer, category, verified
        return item

    def resolve(self, session: Session, request: QuestionRequest) -> str | None:
        if request.category in {"sensitive", "legal"}:
            return None
        item = self.lookup(session, request.question)
        return item.answer if item else None
