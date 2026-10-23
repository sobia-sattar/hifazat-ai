import re

BENIGN_PATTERNS = [
    # Study, exams, learning
    r"\b(?:today is my|have an?|studying for|prep(?:aring)? for|good luck on)?\s*exams?\b",
    r"\b(?:clear and easy|easy to follow|easy to understand|well explained|good explanation)\b",
    r"\b(?:come back to watch|watch it again|watching this again|rewatching)\b",
    r"\b(?:great|good|awesome|amazing|helpful|informative|nice|best)\s+(?:video|explanation|tutorial|content|work|job|lesson)\b",
    r"\b(?:learned a lot|thank(?:s|\s+you)\s+(?:for|so much)?|bohat (?:acha|achha|khoob)|shukriya)\b",
    
    # Music, songs, listening
    r"\blistening\s+(?:to\s+)?(?:this\s+)?(?:song|music|track|beat|in\s+20\d\d)\b",
    r"\b(?:love this (?:song|track|music|voice)|beautiful (?:song|voice|melody))\b",
    r"\b(?:vibe|vibing|nostalgia|nostalgic|masterpiece)\b",
    
    # Poetic lyrics / harmless emotional expressions (not targeted harassment)
    r"\b(?:push me away like i was never exist|never existed? in (?:ur|your) life)\b",
]

HARMFUL_MARKERS = [
    r"\b(?:idiot|stupid|moron|loser|dumb|ugly|disgusting|worthless|trash|garbage|clown|scum)\b",
    r"\b(?:kill|die|murder|destroy|hurt|beat|shoot|punch|strangle|suicide)\b",
    r"\b(?:hate you|hate u|despise|burn in hell)\b",
    r"\b(?:shut up|bitch|bastard|asshole|whore|slut|cunt|f[u*]ck|sh[i*]t|fag)\b",
    r"\b(?:pagal|bewaqoof|kutta|kutte|chutiya|harami|kamine|bakwas|jahil|kanjar|lanat)\b",
    r"\b(?:maroonga|jaan se maar|goli maar)\b",
    r"(?:کتے|حرامی|کمینے|بکواس|پاگل|بیوقوف|لعنت)",
]

def is_benign_intent(text: str) -> bool:
    if not text or not isinstance(text, str):
        return False
    clean = text.lower()
    for pat in HARMFUL_MARKERS:
        if re.search(pat, clean):
            return False
    for pat in BENIGN_PATTERNS:
        if re.search(pat, clean):
            return True
    return False
