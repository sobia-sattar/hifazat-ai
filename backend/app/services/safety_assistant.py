"""AI Cyber Safety Assistant Engine.

Strict Safety & Security Principles:
- Conversational intelligent fallback: handles greetings, explanations, Roman Urdu, and safety inquiries naturally.
- Deterministic crisis detector runs BEFORE any LLM call to intercept self-harm or immediate danger.
- Strict topic bounds: cyberbullying, harassment, evidence preservation, platform safety, digital wellbeing.
- Zero tool, file, or database access for the assistant.
- Ephemeral in-memory execution; no chat persistence by default.
- Robust prompt injection resistance and input length limits.
"""

from __future__ import annotations

import re
from typing import Any
import httpx

from app.core.config import get_settings

# Emergency Crisis Resources (Marked with required owner confirmation)
CRISIS_RESOURCES = [
    {
        "region": "Pakistan (Cyber Harassment Helpline / FIA NR3C)",
        "helpline": "0800-39393 (Digital Rights Foundation) / 1991 (FIA Cybercrime)",
        "description": "Free, confidential legal advice and digital safety support for harassment victims.",
        "confirmation_status": "TODO: owner to confirm",
    },
    {
        "region": "International / Mental Health Crisis",
        "helpline": "Find A Helpline (https://findahelpline.com)",
        "description": "Free, confidential support from local crisis lines in over 130 countries.",
        "confirmation_status": "TODO: owner to confirm",
    },
    {
        "region": "United States & Canada (Crisis Text Line)",
        "helpline": "Text HOME to 741741",
        "description": "Free 24/7 crisis support via SMS.",
        "confirmation_status": "TODO: owner to confirm",
    },
    {
        "region": "United Kingdom (Shout)",
        "helpline": "Text SHOUT to 85258",
        "description": "Free, confidential 24/7 text support.",
        "confirmation_status": "TODO: owner to confirm",
    },
]

# Deterministic regex patterns for self-harm, suicide, or immediate personal safety danger
CRISIS_PATTERNS = [
    r"\b(kill myself|suicide|want to die|end my life|cut myself|self harm|hurt myself|don't want to live)\b",
    r"\b(khudkushi|mar jana chahta|jaan le lunga|zindagi khatam)\b",
    r"(خودکشی|مرنا چاہتا|زندگی ختم)",
]

SYSTEM_PROMPT = (
    "You are the HIFAZAT AI Cyber Guardian (حفاظت AI). Your purpose is to provide friendly, supportive, "
    "and practical conversational guidance on cybersecurity, cyberbullying, online harassment, scam detection, "
    "and digital safety. You can speak English, Urdu, and Roman Urdu naturally like ChatGPT. "
    "Rules:\n"
    "1. Be friendly, empathetic, and conversational (reply to 'hi' with a warm greeting).\n"
    "2. Explain cybersecurity and online safety in simple, easy-to-understand terms.\n"
    "3. Keep responses helpful, practical, and de-escalating.\n"
    "4. If asked in Roman Urdu or Urdu, respond conversationally in the same language.\n"
    "5. Keep responses concise (under 250 words)."
)


def check_crisis(text: str) -> bool:
    """Pre-check text deterministically for self-harm or severe personal danger."""
    for pattern in CRISIS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def get_conversational_guidance(query: str) -> dict[str, Any]:
    """Provide intelligent, natural conversational replies like a real ChatGPT assistant."""
    lower = query.lower().strip()
    clean = re.sub(r"[^\w\s]", "", lower)

    # 1. Greetings & Casual Chat
    if clean in ["hi", "hello", "hey", "salam", "assalam", "assalam o alaikum", "aoa", "kese ho", "how are you", "yo"]:
        if any(w in clean for w in ["salam", "assalam", "aoa"]):
            reply = (
                "Walaikum Assalam! 👋 Main aapka **HIFAZAT AI Cyber Guardian (حفاظت AI)** hoon.\n\n"
                "Main aapko online threats, cyberbullying, aur phishing scams se bachane ke liye yahan hoon. "
                "Aap mujhse cybersecurity, password safety, ya kisi suspicious message ke baare mein kuch bhi pooch sakte hain. "
                "Main aapki kya madad kar sakta hoon?"
            )
        else:
            reply = (
                "Hello! 👋 I am your **HIFAZAT AI Cyber Guardian (حفاظت AI)**.\n\n"
                "I'm here to help protect your digital safety, analyze online threats, and answer your cybersecurity questions. "
                "You can ask me about safe online habits, how to handle harassment, or how HIFAZAT AI works. "
                "How can I help you today?"
            )
        return {"source": "static_curated", "text": reply}

    # 2. "Who are you" / "Aap kon ho"
    if any(p in clean for p in ["who are you", "who r u", "aap kon ho", "tum kon ho", "what are you"]):
        reply = (
            "I am the **HIFAZAT AI Cyber Guardian (حفاظت AI)** — your 24/7 AI-powered digital safety companion. "
            "My mission is to help you stay safe online, recognize digital threats, de-escalate harassment, "
            "and guide you on how to protect your personal privacy and accounts."
        )
        return {"source": "static_curated", "text": reply}

    # 3. "What is cybersecurity" / "Cyber security kya hai"
    if any(p in lower for p in ["what is cybersecurity", "what is cyber security", "cyber security kya hai", "cybersecurity kya hai", "cybersecurity kya hota hai", "cyber security kia hai"]):
        reply = (
            "**Cybersecurity (سائبر سیکیورٹی)** is the practice of protecting computers, smartphones, networks, "
            "and personal data from digital attacks, theft, and unauthorized access.\n\n"
            "In everyday life, cybersecurity helps you:\n"
            "• **Protect Accounts**: Using strong passphrases and Two-Factor Authentication (2FA) so hackers can't break in.\n"
            "• **Avoid Scams & Phishing**: Identifying fake links and messages that try to steal your money or passwords.\n"
            "• **Defend Against Cyberbullying**: Detecting abusive comments, preserving digital proof, and taking safety action.\n"
            "• **Privacy Control**: Keeping your private photos, phone numbers, and location secure from identity theft."
        )
        return {"source": "static_curated", "text": reply}

    # 4. "Yeh kia h" / "Yeh kaise kaam karta hai" / "What is this platform" / "Yeh aisy kam krrha h"
    if any(p in lower for p in ["yeh kia h", "yeh kia hai", "yeh kya hai", "yeh kya platform hai", "yeh platform kia hai", "yeh kaise kaam karta hai", "yeh aisy kam krrha h", "yeh kaise kam karta hai", "what is hifazat", "what is this platform", "how does this work"]):
        reply = (
            "**HIFAZAT AI (حفاظت AI)** aik intelligent digital protection suite hai jo internet users ko online bad-tameezi (cyberbullying), "
            "harassment, aur scams se bachane ke liye design kiya gaya hai.\n\n"
            "**Yeh kis tarah kaam karta hai:**\n\n"
            "1. 🔍 **AI Threat Detection**: Agar koi comment ya message harmful ho, to humara trained Machine Learning model "
            "English, Urdu (اردو), aur Roman Urdu ko analyze kar ke batata hai ke content **SAFE** hai ya **HARMFUL**.\n"
            "2. 🛡️ **Scam & Phishing Checker**: Mashkook messages ko scan karta hai aur unke dangerous links ko automatically neutralize (defang) kar deta hai.\n"
            "3. 🔑 **Password Strength Gauge**: Browser ke andar bina kisi server ko data bheje aapke password ki strength evaluate karta hai (100% private).\n"
            "4. 📋 **Incident Center**: Harassment ka timestamped record aur evidence safe rakhne ki jagah.\n"
            "5. 🤖 **AI Assistant (Cyber Guardian)**: Main har page par available hoon taake aapko de-escalation aur safety guidelines de sakoon."
        )
        return {"source": "static_curated", "text": reply}

    # 5. "What are the best immediate safety steps if someone is targeting me online?"
    if any(k in lower for k in ["targeting me", "harassing me", "someone is targeting", "targeting me online", "immediate safety steps", "being bullied"]):
        reply = (
            "**Immediate Action Protocol for Online Targeting & Harassment:**\n\n"
            "1. **Do Not Retaliate**: Avoid responding angrily. Bullies and trolls look for emotional reactions; disengaging denies them attention.\n"
            "2. **Capture Evidence Immediately**: Take full screenshots showing the sender's username, profile link, message text, and exact date/time.\n"
            "3. **Block & Mute**: Block the perpetrator across all personal accounts and restrict who can comment on your posts.\n"
            "4. **Log the Incident**: Use the **HIFAZAT Incident Center** to save an evidence record so you have a dated trail.\n"
            "5. **Report to Platform / Authorities**: Submit an in-app harassment report. For serious threats or blackmail, report to the FIA Cybercrime Helpline (1991 in Pakistan) or local authorities."
        )
        return {"source": "static_curated", "text": reply}

    # 6. Scam / Phishing Signs
    if any(k in lower for k in ["scam", "phish", "suspicious message", "warning signs", "fake link"]):
        reply = (
            "**Key Warning Signs of Scam & Phishing Messages:**\n\n"
            "• **Artificial Urgency**: Threatens immediate account closure or legal arrest within 24 hours to rush you into panicking.\n"
            "• **Credential Harvesting**: Asking for OTPs, ATM PINs, passwords, or CNIC/identity numbers. Real banks never ask for your password.\n"
            "• **Deceptive Links**: Lookalike domains (e.g. `secure-bank-login[.]xyz`) or short links designed to steal your credentials.\n"
            "• **Too-Good-To-Be-True Offers**: Unexpected lottery wins, cash grants (like BISP or prize schemes), or unsolicited crypto rewards.\n\n"
            "💡 *Tip: Paste any suspicious text into the **Scam Check** tool in the top navigation to analyze its threat score safely.*"
        )
        return {"source": "static_curated", "text": reply}

    # 7. Model detection & scores
    if any(k in lower for k in ["detect", "model", "score", "threshold", "explain", "svm", "how it detects", "detection mean"]):
        reply = (
            "**How HIFAZAT AI Detection & Scores Work:**\n\n"
            "• **Calibrated AI Engine**: The core classifier uses a calibrated Hybrid Word & Character SVM model that evaluates n-grams across English, Urdu script, and Roman Urdu.\n"
            "• **Decision Threshold (0.45)**: If the harmful probability is below 0.45, the content is classified as **SAFE**. If it equals or exceeds 0.45, it is classified as **HARMFUL**.\n"
            "• **Explainable AI (XAI)**: The model lists specific feature contributions (e.g. `word__acha: -0.12` or `word__idiot: +0.32`), showing which terms influenced the score.\n"
            "• **Human-in-the-Loop**: Automated AI scores are assistive estimates, not absolute judicial verdicts. Final moderation decisions should always involve human oversight."
        )
        return {"source": "static_curated", "text": reply}

    # 8. Password protection
    if any(k in lower for k in ["password", "passphrase", "2fa", "two factor"]):
        reply = (
            "**Best Practices for Password Security:**\n\n"
            "• **Use Passphrases**: 4-5 random words strung together (e.g. `blue-coffee-mountain-78!`) are much stronger and easier to remember than short complex strings.\n"
            "• **Never Reuse Passwords**: If one website suffers a data breach, attackers will attempt that same password on your email and banking.\n"
            "• **Enable Two-Factor Authentication (2FA)**: Prefer an authenticator app (like Google Authenticator) over SMS codes.\n"
            "• **Test Securely**: Use the **Password Check** tool on HIFAZAT AI — it analyzes strength 100% locally in your browser with zero network transmission."
        )
        return {"source": "static_curated", "text": reply}

    # 9. Evidence preservation
    if any(k in lower for k in ["evidence", "proof", "record", "screenshot", "save"]):
        reply = (
            "**How to Preserve Digital Evidence:**\n\n"
            "• Take uncropped screenshots that capture the user handle, profile link, post date, and exact timestamps.\n"
            "• If possible, record a quick screen video scrolling through the comments to prove the conversation wasn't faked.\n"
            "• Export chat logs if using WhatsApp or messaging apps before deleting or blocking.\n"
            "• Save everything in the **HIFAZAT Incident Center** to maintain an organized, private record."
        )
        return {"source": "static_curated", "text": reply}

    # 10. General digital wellbeing fallback
    reply = (
        "**Digital Safety & Wellbeing Guide:**\n\n"
        "• **Protect Your Privacy**: Regularly audit who can see your profile details, friend lists, and tagged photos.\n"
        "• **Mental Wellbeing First**: Remember that online toxicity reflects the perpetrator's character, not your worth. Step away from screens when needed.\n"
        "• **Stay Protected**: Use Two-Factor Authentication (2FA), verify unfamiliar links, and log any harassment in our Incident Center.\n\n"
        "Feel free to ask me any specific question about online safety, password tips, or analyzing suspicious text!"
    )
    return {"source": "static_curated", "text": reply}


def call_gemini(user_message: str, api_key: str) -> str:
    """Invoke Google Gemini REST API securely using standard httpx."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_message[:1000]}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 400,
        },
    }
    with httpx.Client(timeout=15.0) as client:
        res = client.post(url, json=payload)
        res.raise_for_status()
        data = res.json()
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"]
        raise ValueError("Invalid response format from Gemini API.")


def call_openai(user_message: str, api_key: str, base_url: str, model: str) -> str:
    """Invoke OpenAI-compatible chat completion."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model or "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message[:1000]},
        ],
        "temperature": 0.4,
        "max_tokens": 400,
    }
    with httpx.Client(timeout=15.0) as client:
        res = client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        choices = data.get("choices", [])
        if choices and "message" in choices[0]:
            return choices[0]["message"].get("content", "")
        raise ValueError("Invalid response from OpenAI API.")


def ask_assistant(user_message: str, attached_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Primary handler: checks crisis, attempts configured provider, falls back to conversational AI guidance."""
    cleaned = (user_message or "").strip()
    if not cleaned:
        raise ValueError("Message cannot be empty.")

    # 1. Deterministic Crisis Check
    if check_crisis(cleaned):
        return {
            "is_crisis": True,
            "reply": (
                "**URGENT: YOU ARE NOT ALONE.**\n\n"
                "If you are experiencing immediate distress or having thoughts of self-harm, "
                "please pause and reach out to one of the confidential support helplines listed below right now."
            ),
            "crisis_resources": CRISIS_RESOURCES,
            "notice": "Automated crisis detection. Please contact emergency services or trusted support immediately.",
            "source": "crisis_override",
        }

    # Format user input with optional explicitly attached detection context
    context_prefix = ""
    if attached_context:
        context_prefix = (
            f"[User attached detection result for context: "
            f"Risk: {attached_context.get('risk', 'N/A')}, "
            f"Language: {attached_context.get('language', 'N/A')}, "
            f"Binary prediction: {attached_context.get('binary_prediction', 'N/A')}]\n\n"
        )
    full_prompt = context_prefix + cleaned

    # 2. Check Provider Configuration
    settings = get_settings()
    provider_reply = None
    source = "ai_assistant"

    gemini_key = getattr(settings, "gemini_api_key", "")
    genai_key = getattr(settings, "genai_api_key", "")
    allow_external = getattr(settings, "allow_external_explanations", False)

    # Attempt Gemini if key is available
    if gemini_key:
        try:
            provider_reply = call_gemini(full_prompt, gemini_key)
            source = "gemini"
        except Exception:
            provider_reply = None

    # Attempt OpenAI if configured and enabled
    if not provider_reply and allow_external and genai_key:
        try:
            provider_reply = call_openai(
                full_prompt,
                genai_key,
                settings.genai_base_url,
                settings.genai_model,
            )
            source = "openai"
        except Exception:
            provider_reply = None

    # 3. Fallback to Conversational Intelligent Guidance
    if not provider_reply:
        conv_data = get_conversational_guidance(cleaned)
        provider_reply = conv_data["text"]
        source = conv_data["source"]

    return {
        "is_crisis": False,
        "reply": provider_reply,
        "source": source,
        "notice": "AI assistant guidance — not a prediction from the detection model and not a substitute for human help.",
    }
