from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from config import Settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()
        self.mock_mode = not bool(self.settings.gemini_api_key)
        self._client = None
        if not self.mock_mode:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.settings.gemini_api_key)
            except Exception as exc:
                logger.warning("Gemini unavailable; using deterministic mock mode: %s", exc)
                self.mock_mode = True

    def generate_json(self, prompt: str, response_model: type[T], mock_payload: dict[str, Any] | None = None) -> T:
        if self.mock_mode or self._client is None:
            return response_model.model_validate(mock_payload or {})
        try:
            response = self._client.models.generate_content(model=self.settings.gemini_model, contents=prompt, config={"response_mime_type": "application/json", "response_schema": response_model})
            text = getattr(response, "text", "")
            return response_model.model_validate(json.loads(text))
        except Exception:
            logger.exception("Gemini request failed")
            raise
