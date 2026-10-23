"""HIFAZAT AI (حفاظت AI) backend application package."""
import sys
from pathlib import Path

# Automatically inject repo root (for src) and backend root (for app) into sys.path
_repo_root = Path(__file__).resolve().parents[2]
_backend_root = Path(__file__).resolve().parents[1]
for _p in [str(_repo_root), str(_backend_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
