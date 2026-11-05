from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FormField:
    name: str
    label: str
    input_type: str
    required: bool = False
    options: list[str] | None = None


def _fields_from_html(html: str) -> list[FormField]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError("beautifulsoup4 is required for HTML form detection") from exc
    soup = BeautifulSoup(html, "html.parser"); result = []
    for element in soup.select("input, textarea, select"):
        name = element.get("name") or element.get("id") or ""
        if not name: continue
        label_node = soup.find("label", attrs={"for": element.get("id")})
        label = label_node.get_text(" ", strip=True) if label_node else (element.get("aria-label") or element.get("placeholder") or name)
        options = [option.get_text(" ", strip=True) for option in element.select("option")] if element.name == "select" else None
        result.append(FormField(name, label, element.get("type", element.name), element.has_attr("required"), options))
    return result


class FormDetector:
    def detect_html(self, html: str) -> list[FormField]:
        return _fields_from_html(html)

    async def detect_page(self, page: Any) -> list[FormField]:
        return _fields_from_html(await page.content())
