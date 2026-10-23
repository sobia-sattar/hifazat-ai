"""Only configured, license-reviewed sources can be downloaded."""

from datetime import datetime, timezone
import urllib.request
import yaml
from src.utils.common import ROOT, digest, write_json


def main():
    config = yaml.safe_load((ROOT / "configs/data.yaml").read_text())
    records = []
    for source in config["sources"]:
        if not source["approved"] or not source.get("download_url"):
            continue
        if not source.get("license_evidence"):
            raise ValueError("Missing license evidence")
        destination = (ROOT / source["path"]).resolve()
        if not destination.is_relative_to((ROOT / "data/raw").resolve()):
            raise ValueError("Destination outside raw data directory")
        acquired = datetime.now(timezone.utc).isoformat()
        if not destination.exists():
            temp = destination.with_suffix(destination.suffix + ".part")
            with urllib.request.urlopen(source["download_url"], timeout=60) as response, temp.open("wb") as out:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    out.write(chunk)
            temp.replace(destination)
        else:
            acquired = "unknown (cached before acquisition log)"
        records.append(dict(source=source["id"], date_acquired=acquired, sha256=digest(destination)))
    write_json(ROOT / "data/acquisition.json", records)


if __name__ == "__main__":
    main()
