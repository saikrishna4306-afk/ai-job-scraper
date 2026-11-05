from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ApplicationAdapter(ABC):
    name = "generic"

    @abstractmethod
    async def fill(self, page: Any, values: dict[str, str], resume_path: str | None = None, cover_letter_path: str | None = None) -> list[dict]:
        raise NotImplementedError

    async def confirmation(self, page: Any) -> dict[str, str] | None:
        text = (await page.locator("body").inner_text()).lower()
        markers = ("thank you", "application received", "application submitted", "successfully applied")
        if any(marker in text for marker in markers):
            return {"evidence": text[:1000]}
        return None


class GenericHtmlAdapter(ApplicationAdapter):
    name = "generic"

    async def fill(self, page: Any, values: dict[str, str], resume_path: str | None = None, cover_letter_path: str | None = None) -> list[dict]:
        for name, value in values.items():
            locator = page.locator(f"[name='{name}'], #{name}").first
            if await locator.count():
                await locator.fill(value)
        if resume_path:
            upload = page.locator("input[type='file']").first
            if await upload.count(): await upload.set_input_files(resume_path)
        return []


class GreenhouseAdapter(GenericHtmlAdapter): name = "greenhouse"
class LeverAdapter(GenericHtmlAdapter): name = "lever"
class AshbyAdapter(GenericHtmlAdapter): name = "ashby"
