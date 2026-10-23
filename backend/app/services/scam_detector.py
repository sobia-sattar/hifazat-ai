"""Deterministic Scam and Phishing Pattern Detector.

Strict Security Boundaries:
- Never fetches, resolves, previews, or visits URLs found in user text.
- Neutralizes all URLs (e.g. 'http' -> 'hxxp', rendered as inert non-clickable tokens).
- Does not persist or store submitted text.
- Operates independently from the ML cyberbullying classifier.
- Never guarantees or certifies that any message is safe or legitimate.
"""

from __future__ import annotations

import re
from typing import Any

# Defanging regex for URLs and domains
URL_REGEX = re.compile(
    r'(https?://[^\s<>"]+|www\.[^\s<>"]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>"]*)?)',
    re.IGNORECASE,
)

# Heuristic Rule Definitions with Multilingual Patterns (English + Roman Urdu + Urdu)
RULES: list[dict[str, Any]] = [
    {
        "id": "urgency",
        "category": "High Urgency / Pressure Tactics",
        "description": "Demands immediate action or threatens swift account suspension, legal action, or loss of access.",
        "patterns": [
            r"\b(act now|immediately|urgent|within (?:24|48|12) hours|account (?:suspended|closed|blocked|locked)|final notice|legal action|arrest warrant)\b",
            r"\b(foran|jaldi karo|account band|block ho jaye ga|akhri notice|warn kar rahe hain)\b",
            r"(فوراً|اکاؤنٹ بند|قانونی کارروائی|آخری نوٹس)",
        ],
        "weight": 2,
    },
    {
        "id": "financial",
        "category": "Financial or Payment Demands",
        "description": "Requests funds transfer, cryptocurrency, gift cards, or unsolicited cash payments.",
        "patterns": [
            r"\b(wire transfer|western union|crypto(?:currency)?|bitcoin|btc|usdt|gift card|send money|pay fee|advance fee|claim reward|lottery prize|cash prize)\b",
            r"\b(paise bhejo|rakam transfer|inami scheme|lottery nikal aayi|bisp|easypaisa karo|jazzcash karo)\b",
            r"(پیسے بھیجو|رقم ٹرانسفر|انعامی سکیم|لاٹری)",
        ],
        "weight": 2,
    },
    {
        "id": "credentials",
        "category": "Credential & Sensitive Data Harvesting",
        "description": "Solicits passwords, OTPs, verification PINs, credit card CVV, or identity numbers.",
        "patterns": [
            r"\b(enter (?:your )?password|confirm (?:your )?pin|share (?:your )?otp|one-time password|security code|verify (?:your )?identity|card details|cvv|ssn|cnic)\b",
            r"\b(password batao|pin code do|otp share karo|shanakhti card|cnic number)\b",
            r"(پاس ورڈ|او ٹی پی|شناختی کارڈ)",
        ],
        "weight": 3,
    },
    {
        "id": "impersonation",
        "category": "Authority or Brand Impersonation",
        "description": "Claims to represent official support, customs, law enforcement, or corporate security departments.",
        "patterns": [
            r"\b(official support|helpdesk|customs department|security team|apple support|microsoft tech support|tax department|fbi|fbr|state bank)\b",
            r"\b(head office se bol rahe|security team ka call|fbr notice)\b",
            r"(اسٹیٹ بینک|سیکیورٹی ٹیم)",
        ],
        "weight": 1,
    },
    {
        "id": "suspicious_links",
        "category": "Suspicious Link / Insecure Domain Format",
        "description": "Contains direct IP addresses, non-standard URL shorteners, or deceptive lookalike domains.",
        "patterns": [
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            r"\b(bit\.ly|tinyurl\.com|t\.co|goo\.gl|is\.gd|ow\.ly|buff\.ly|cutt\.ly)/[^\s]+",
            r"\b[a-zA-Z0-9-]+\.(xyz|top|work|click|gq|cf|ml|tk|fit)\b",
        ],
        "weight": 2,
    },
]


def defang_url(url: str) -> str:
    """Neutralize a URL so it cannot be automatically parsed or opened as a live link."""
    neutral = url.replace("http://", "hxxp://").replace("https://", "hxxps://")
    # Replace period before TLD or slash with [.]
    neutral = re.sub(r'\.([a-zA-Z]{2,6})(?=[/?#]|$)', r'[.]\1', neutral)
    return neutral


def analyze_scam_text(text: str) -> dict[str, Any]:
    """Inspect text for heuristic scam indicators and neutralize embedded URLs."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    cleaned_text = text.strip()
    raw_urls = URL_REGEX.findall(cleaned_text)

    # Neutralize every discovered URL
    defanged_urls: list[dict[str, str]] = []
    inert_text = cleaned_text
    for raw in set(raw_urls):
        defanged = defang_url(raw)
        defanged_urls.append({"original_preview": raw[:60], "defanged": defanged})
        inert_text = inert_text.replace(raw, defanged)

    triggered_rules: list[dict[str, Any]] = []
    total_score = 0
    matched_phrases: list[str] = []

    for rule in RULES:
        rule_matches: list[str] = []
        for pat in rule["patterns"]:
            found = re.findall(pat, cleaned_text, re.IGNORECASE)
            for m in found:
                phrase = m if isinstance(m, str) else m[0]
                if phrase and phrase not in rule_matches:
                    rule_matches.append(phrase)

        if rule_matches:
            triggered_rules.append({
                "id": rule["id"],
                "category": rule["category"],
                "description": rule["description"],
                "matches": rule_matches,
                "weight": rule["weight"],
            })
            total_score += rule["weight"]
            matched_phrases.extend(rule_matches)

    # Risk level categorization
    # HIGH: score >= 3 (credential harvesting alone, weight=3, is high-risk)
    #       OR 2+ different rule categories triggered with combined score >= 3
    #       OR total score >= 4
    if total_score >= 3 or (len(triggered_rules) >= 2 and total_score >= 2):
        risk_level = "Many warning signs found"
        risk_class = "HIGH"
    elif total_score >= 1:
        risk_level = "Some warning signs found"
        risk_class = "MEDIUM"
    else:
        risk_level = "No strong warning signs found"
        risk_class = "LOW"

    return {
        "risk_level": risk_level,
        "risk_class": risk_class,
        "score": total_score,
        "triggered_rules": triggered_rules,
        "matched_phrases": list(set(matched_phrases)),
        "defanged_urls": defanged_urls,
        "inert_preview": inert_text[:1500],
        "notice": (
            "Automated heuristic rule check. Never consider any message verified or safe based solely "
            "on this result. Always authenticate communications directly through official, verified channels."
        ),
        "url_warning": (
            "Embedded links have been defanged (e.g. hxxps://) to prevent accidental navigation. "
            "Never visit unverified links provided in suspicious messages."
        ),
    }
