import os
import sys
from pathlib import Path

# Ensure repo root and backend root are both in sys.path
ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
for p in [str(ROOT), str(BACKEND)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[HIFAZAT AI] Starting backend server on {host}:{port} ...")
    uvicorn.run("app.main:app", app_dir=str(BACKEND), host=host, port=port)
