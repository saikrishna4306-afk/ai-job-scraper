from __future__ import annotations

from pathlib import Path
from typing import Any


def _fallback_text(content: dict[str, Any], path: Path) -> None:
    path.with_suffix(".txt").write_text("\n".join([content.get("name", ""), content.get("summary", ""), "Skills: " + ", ".join(content.get("skills", []))]), encoding="utf-8")


def write_resume_pdf(content: dict[str, Any], path: str | Path) -> Path:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        styles = getSampleStyleSheet(); story = []
        story.append(Paragraph(content.get("name", "Candidate"), styles["Title"]))
        contact = " | ".join([content.get("email", ""), content.get("phone", ""), content.get("location", "")] + content.get("links", []))
        story.append(Paragraph(contact, styles["Normal"])); story.append(Spacer(1, 0.12 * inch))
        for heading, value in (("Professional Summary", content.get("summary", "")), ("Skills", ", ".join(content.get("skills", []))), ("Experience", content.get("experience", [])), ("Projects", content.get("projects", [])), ("Education", content.get("education", [])), ("Certifications", content.get("certifications", []))):
            story.append(Paragraph(heading, styles["Heading2"]))
            if isinstance(value, list):
                for item in value:
                    story.append(Paragraph(str(item.get("name", item)) if isinstance(item, dict) else str(item), styles["BodyText"]))
            else:
                story.append(Paragraph(str(value), styles["BodyText"]))
            story.append(Spacer(1, 0.08 * inch))
        SimpleDocTemplate(str(path), pagesize=LETTER, rightMargin=0.55 * inch, leftMargin=0.55 * inch, topMargin=0.5 * inch, bottomMargin=0.5 * inch).build(story)
    except ImportError:
        _fallback_text(content, path)
    return path
