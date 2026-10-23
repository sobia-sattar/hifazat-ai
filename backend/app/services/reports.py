from __future__ import annotations

import csv
import io
import json
from html import escape
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph as ReportParagraph, SimpleDocTemplate, Spacer


def Paragraph(text, style):
    # Untrusted comment text must never become ReportLab markup or image URLs.
    return ReportParagraph(escape(str(text)), style)


LIMITATIONS = (
    "Limitations: No NLP system can guarantee 100% accuracy for sarcasm, slang, spelling variation, "
    "code-mixing, Roman Urdu, or context-dependent language. Confidence is calibrated on validation data "
    "when a trained model is available. Demo-mode comments must not be used for research claims. "
    "AI predictions may contain errors. High-risk content should be reviewed by a human moderator."
)


def spreadsheet_safe(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def comments_csv(payload: dict) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "comment", "language", "classification", "category", "confidence", "risk"])
    for c in payload.get("comments") or []:
        w.writerow(
            [
                c.get("id"),
                spreadsheet_safe(c.get("original_text")),
                c.get("language"),
                c.get("classification"),
                c.get("category"),
                c.get("confidence"),
                c.get("risk"),
            ]
        )
    return buf.getvalue().encode("utf-8")


def comments_json(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def comments_pdf(payload: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    video = payload.get("video") or {}
    stats = payload.get("stats") or {}
    story.append(Paragraph("HIFAZAT AI Analysis Report", styles["Title"]))
    story.append(Paragraph("Your Digital World, Your Protection.", styles["Italic"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated: {datetime.utcnow().isoformat()}Z", styles["Normal"]))
    story.append(Paragraph(f"Video: {video.get('title') or 'n/a'}", styles["Normal"]))
    story.append(Paragraph(f"Channel: {video.get('channel') or 'n/a'}", styles["Normal"]))
    story.append(Paragraph(f"Video ID: {video.get('video_id') or 'n/a'}", styles["Normal"]))
    story.append(Paragraph(f"Analysis date: {payload.get('created_at')}", styles["Normal"]))
    story.append(Paragraph(f"Model: {payload.get('model_name')}", styles["Normal"]))
    story.append(Paragraph(f"Demo mode: {payload.get('demo_mode')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    total = stats.get("total") or 0
    safe_pct = round(100 * (stats.get("safe") or 0) / total, 2) if total else "Not available"
    story.append(Paragraph(f"Total comments: {total}", styles["Normal"]))
    story.append(Paragraph(f"Safe percentage: {safe_pct}", styles["Normal"]))
    story.append(Paragraph(f"Bullying percentage: {stats.get('bullying_rate')}", styles["Normal"]))
    story.append(Paragraph(f"Category distribution: {stats.get('category_distribution')}", styles["Normal"]))
    story.append(Paragraph(f"Language distribution: {stats.get('language_distribution')}", styles["Normal"]))
    story.append(Paragraph(f"Risk distribution: {stats.get('risk_distribution')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("High-risk comments", styles["Heading2"]))
    highs = [c for c in payload.get("comments") or [] if c.get("risk") in {"HIGH", "CRITICAL"}]
    if not highs:
        story.append(Paragraph("None in this analysis.", styles["Normal"]))
    for c in highs[:30]:
        story.append(
            Paragraph(
                f"[{c.get('risk')}] ({c.get('language')}, {c.get('confidence')}) {c.get('original_text')}",
                styles["Normal"],
            )
        )
    story.append(Spacer(1, 12))
    story.append(Paragraph("XAI observations", styles["Heading2"]))
    story.append(
        Paragraph(
            "Explanations use linear TF-IDF coefficients when a linear model is selected, otherwise token occlusion.",
            styles["Normal"],
        )
    )
    story.append(Paragraph("GenAI summary", styles["Heading2"]))
    story.append(Paragraph(str(stats.get("genai_summary") or "GenAI explanation unavailable. Model and XAI results remain available."), styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(LIMITATIONS, styles["Normal"]))
    if payload.get("demo_mode"):
        story.append(Paragraph(str(payload.get("demo_notice")), styles["Normal"]))
    doc.build(story)
    return buf.getvalue()
