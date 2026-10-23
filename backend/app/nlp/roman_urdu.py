"""Roman Urdu normalization for informal social-media spelling variation.

Preserves the original string elsewhere; this module only returns a normalized copy.
"""

from __future__ import annotations

import re
from functools import lru_cache

# Common Roman Urdu lexical variants → canonical form.
# This is a linguistic resource, not a labeled toxicity dataset.
VARIANT_MAP: dict[str, str] = {
    "bohat": "bohat",
    "bahut": "bohat",
    "boht": "bohat",
    "bht": "bohat",
    "bhut": "bohat",
    "bahot": "bohat",
    "acha": "acha",
    "achha": "acha",
    "accha": "acha",
    "achi": "achi",
    "achhi": "achi",
    "hai": "hai",
    "hy": "hai",
    "he": "hai",
    "hain": "hain",
    "hen": "hain",
    "hn": "hain",
    "nahi": "nahi",
    "nahin": "nahi",
    "nai": "nahi",
    "nhi": "nahi",
    "nh": "nahi",
    "ni": "nahi",
    "nae": "nahi",
    "tum": "tum",
    "tm": "tum",
    "tumm": "tum",
    "tu": "tu",
    "tujhe": "tujhe",
    "tujhy": "tujhe",
    "tjhe": "tujhe",
    "mujhe": "mujhe",
    "mujhy": "mujhe",
    "mjhe": "mujhe",
    "mjy": "mujhe",
    "mjhy": "mujhe",
    "kya": "kya",
    "kia": "kya",
    "kiaa": "kya",
    "kiya": "kya",
    "kyun": "kyun",
    "kun": "kyun",
    "q": "kyun",
    "kyon": "kyun",
    "aap": "aap",
    "ap": "aap",
    "apko": "aapko",
    "aapko": "aapko",
    "apka": "aapka",
    "aapka": "aapka",
    "apki": "aapki",
    "aapki": "aapki",
    "mera": "mera",
    "meri": "meri",
    "mere": "mere",
    "hum": "hum",
    "hm": "hum",
    "yeh": "yeh",
    "ye": "yeh",
    "yah": "yeh",
    "woh": "woh",
    "wo": "woh",
    "vo": "woh",
    "wah": "woh",
    "ka": "ka",
    "ki": "ki",
    "ke": "ke",
    "ko": "ko",
    "se": "se",
    "mein": "mein",
    "men": "mein",
    "me": "mein",
    "mai": "mein",
    "main": "mein",
    "par": "par",
    "per": "par",
    "pe": "par",
    "aur": "aur",
    "or": "aur",
    "lekin": "lekin",
    "lakin": "lekin",
    "magar": "magar",
    "phir": "phir",
    "fir": "phir",
    "ab": "ab",
    "abhi": "abhi",
    "abi": "abhi",
    "bahut": "bohat",
    "zyada": "zyada",
    "zada": "zyada",
    "zyadah": "zyada",
    "bohot": "bohat",
    "theek": "theek",
    "thik": "theek",
    "thek": "theek",
    "galat": "galat",
    "ghalat": "galat",
    "buray": "buray",
    "bure": "buray",
    "bura": "bura",
    "burai": "burai",
    "bewaqoof": "bewaqoof",
    "bewakoof": "bewaqoof",
    "bewaqoof": "bewaqoof",
    "bewqoof": "bewaqoof",
    "pagal": "pagal",
    "paagal": "pagal",
    "bakwas": "bakwas",
    "bakwaas": "bakwas",
    "becar": "bekar",
    "bekar": "bekar",
    "bekaar": "bekar",
    "ghatiya": "ghatiya",
    "ghatia": "ghatiya",
    "kamina": "kamina",
    "kameena": "kamina",
    "harami": "harami",
    "haraami": "harami",
    "ullu": "ullu",
    "uloo": "ullu",
    "gadha": "gadha",
    "gadhe": "gadha",
    "kutta": "kutta",
    "kutte": "kutta",
    "kutiya": "kutiya",
    "lanat": "laanat",
    "laanat": "laanat",
    "sharam": "sharam",
    "sharm": "sharam",
    "mar": "mar",
    "maar": "maar",
    "mardunga": "maardunga",
    "mardugi": "maardungi",
    "jao": "jao",
    "jaao": "jao",
    "chup": "chup",
    "chupp": "chup",
    "band": "band",
    "karo": "karo",
    "kro": "karo",
    "dekho": "dekho",
    "dekhoo": "dekho",
    "suno": "suno",
    "samajh": "samajh",
    "samaj": "samajh",
    "samajho": "samajho",
    "video": "video",
    "content": "content",
    "channel": "channel",
}

ROMAN_URDU_LEXICON = set(VARIANT_MAP.keys()) | set(VARIANT_MAP.values()) | {
    "haan",
    "han",
    "jee",
    "ji",
    "bhai",
    "behen",
    "bahen",
    "dost",
    "yaar",
    "yar",
    "log",
    "insaan",
    "insan",
    "zindagi",
    "baat",
    "bat",
    "baatein",
    "baatain",
    "gussa",
    "ghussa",
    "naraz",
    "nafrat",
    "badtameez",
    "badtameezi",
    "behaya",
    "fazool",
    "fazul",
    "bewajah",
    "wajah",
    "wajha",
    "kyunki",
    "kiunke",
    "isliye",
    "isliy",
    "phir",
    "warna",
    "agar",
    "agr",
    "toh",
    "to",
    "hi",
    "bhi",
    "bi",
    "sirf",
    "bilkul",
    "bilkl",
    "sakta",
    "sakti",
    "sakte",
    "chahiye",
    "chahye",
    "chahie",
    "hona",
    "hone",
    "karna",
    "kerna",
    "krna",
    "jana",
    "aana",
    "ana",
    "dena",
    "lena",
    "bol",
    "bolo",
    "bolna",
    "keh",
    "kaho",
    "kehta",
    "kehti",
    "dekha",
    "dekhi",
    "suna",
    "lagta",
    "lagti",
    "laga",
    "raha",
    "rahi",
    "rahe",
    "gaya",
    "gayi",
    "gaye",
    "hua",
    "hui",
    "huye",
    "tha",
    "thi",
    "the",
    "hogaya",
    "hogayi",
    "kharab",
    "khrab",
    "ganda",
    "gandi",
    "fool",
    "jahil",
    "nalayak",
    "nalaiq",
    "bewakoof",
    "stupid",
}

_TOKEN = re.compile(r"[A-Za-z]+|[^\sA-Za-z0-9]+|\d+")
_REPEAT = re.compile(r"(.)\1{2,}")


def collapse_repeats(token: str) -> str:
    return _REPEAT.sub(r"\1\1", token)


def normalize_token(token: str) -> str:
    if not token.isalpha():
        return token
    lower = collapse_repeats(token.lower())
    if lower in VARIANT_MAP:
        mapped = VARIANT_MAP[lower]
        if token.isupper():
            return mapped.upper()
        if token[0].isupper():
            return mapped.capitalize()
        return mapped
    return lower


def normalize_roman_urdu(text: str) -> str:
    parts = _TOKEN.findall(text)
    if not parts:
        return text.strip()
    out: list[str] = []
    for i, p in enumerate(parts):
        if p.isalpha():
            out.append(normalize_token(p))
        else:
            out.append(p)
    # Reconstruct with spaces around alphabetic tokens.
    s = ""
    for p in out:
        if not s:
            s = p
        elif p.isalpha() and s[-1].isalnum():
            s += " " + p
        elif not p.isalpha() and p not in ".,!?;:'\")":
            s += p if p.startswith(" ") or s.endswith(" ") else (" " + p if p.isalpha() else p)
        else:
            s += p
    return re.sub(r"\s+", " ", s).strip()


@lru_cache(maxsize=1)
def roman_urdu_lexicon() -> set[str]:
    return {w.lower() for w in ROMAN_URDU_LEXICON}
