from __future__ import annotations

from pathlib import Path


def write_interview_pdf(text: str, path: str | Path) -> Path:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        styles = getSampleStyleSheet(); story = []
        for line in text.splitlines():
            style = styles["Heading2"] if line.startswith("## ") else styles["Heading1"] if line.startswith("# ") else styles["BodyText"]
            story.append(Paragraph(line.lstrip("# ") or " ", style)); story.append(Spacer(1, 6))
        SimpleDocTemplate(str(path), pagesize=LETTER).build(story)
    except ImportError:
        path.with_suffix(".txt").write_text(text, encoding="utf-8")
    return path
