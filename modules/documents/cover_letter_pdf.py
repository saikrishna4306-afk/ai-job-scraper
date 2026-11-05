from __future__ import annotations

from pathlib import Path


def write_cover_letter_pdf(text: str, path: str | Path) -> Path:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        story = []
        for paragraph in text.split("\n\n"):
            story.append(Paragraph(paragraph.replace("\n", "<br/>"), getSampleStyleSheet()["BodyText"])); story.append(Spacer(1, 0.15 * inch))
        SimpleDocTemplate(str(path), pagesize=LETTER, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=0.7 * inch, bottomMargin=0.7 * inch).build(story)
    except ImportError:
        path.with_suffix(".txt").write_text(text, encoding="utf-8")
    return path
