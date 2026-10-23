"""Download publicly documented research datasets. Never invent rows."""

from __future__ import annotations

import json
import ssl
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REGISTRY = ROOT / "research" / "dataset_registry.json"

SOURCES = [
    {
        "id": "davidson2017",
        "name": "Hate Speech and Offensive Language (Davidson et al., 2017)",
        "language": "English",
        "license": "Public research release accompanying ICWSM 2017 paper; see GitHub repository.",
        "url": "https://raw.githubusercontent.com/t-davidson/hate-speech-and-offensive-language/master/data/labeled_data.csv",
        "filename": "davidson_labeled_data.csv",
        "labels": "hate_speech / offensive_language / neither",
    },
    {
        "id": "adeeba2024_train",
        "name": "Urdu Cyberbullying Corpus train (Adeeba, 2024)",
        "language": "Urdu",
        "license": "Public GitHub/Zenodo research corpus (Adeeba, 2024). Verify license in the source repository before redistribution.",
        "url": "https://raw.githubusercontent.com/farahadeeba/cyberbullyingcorpus/main/train_bullying.xlsx",
        "filename": "urdu_train_bullying.xlsx",
        "labels": "as provided in source spreadsheet",
    },
    {
        "id": "adeeba2024_test",
        "name": "Urdu Cyberbullying Corpus test (Adeeba, 2024)",
        "language": "Urdu",
        "license": "Public GitHub/Zenodo research corpus (Adeeba, 2024). Verify license in the source repository before redistribution.",
        "url": "https://raw.githubusercontent.com/farahadeeba/cyberbullyingcorpus/main/test_bullying.xlsx",
        "filename": "urdu_test_bullying.xlsx",
        "labels": "as provided in source spreadsheet",
    },
    {
        "id": "roman_urdu_toxic_hf",
        "name": "Roman-Urdu-Toxic-Corpus (Hugging Face, CC-BY-4.0)",
        "language": "Roman Urdu",
        "license": "CC-BY-4.0",
        "url": "https://huggingface.co/datasets/hafiz-hassaan-saeed/Roman-Urdu-Toxic-Corpus/resolve/main/Roman_Urdu_Toxic_Corpus.csv",
        "filename": "roman_urdu_toxic_corpus.csv",
        "labels": "toxic / non-toxic as provided by the dataset card",
        "optional": True,
    },
]


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "BullyLens-X/1.0 research-acquire"})
    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp, dest.open("wb") as f:
        f.write(resp.read())


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    records = []
    for src in SOURCES:
        dest = RAW / src["filename"]
        rec = dict(src)
        rec["path"] = str(dest.relative_to(ROOT))
        try:
            if dest.exists() and dest.stat().st_size > 0:
                rec["status"] = "cached"
                rec["bytes"] = dest.stat().st_size
            else:
                download(src["url"], dest)
                rec["status"] = "downloaded"
                rec["bytes"] = dest.stat().st_size
        except Exception as exc:
            rec["status"] = "unavailable"
            rec["error"] = str(exc)
            rec["bytes"] = 0
            if dest.exists() and dest.stat().st_size == 0:
                dest.unlink()
        records.append(rec)
        print(f"{src['id']}: {rec['status']} ({rec.get('bytes', 0)} bytes)")
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps({"datasets": records}, indent=2), encoding="utf-8")
    print(f"Wrote {REGISTRY}")


if __name__ == "__main__":
    main()
