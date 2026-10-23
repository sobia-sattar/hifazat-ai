import sys
from pathlib import Path

# Ensure repo root and backend dir are in sys.path for cloud deployments
_repo_root = Path(__file__).resolve().parents[2]
_backend_dir = Path(__file__).resolve().parents[1]
for _p in [str(_repo_root), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.database.session import init_db
from app.api.research_v2 import router as research_router
from app.api.moderation import router as moderation_router
from app.api.channel_scan import router as channel_router
from app.api.safety_assistant import router as assistant_router
from app.api.scam_checker import router as scam_router
from app.api.incident_reports import router as incident_router
from app.core.security import LocalBoundaryMiddleware

settings = get_settings()
app = FastAPI(title="HIFAZAT AI", version="1.0.0", docs_url="/api/docs", redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.public_deployment else (settings.cors_origin_list + ["http://localhost:5173", "http://127.0.0.1:5173"]),
    allow_origin_regex=r"https://.*" if settings.public_deployment else None,
    allow_credentials=not settings.public_deployment,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LocalBoundaryMiddleware)


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(status_code=500, content={"message": "An internal error occurred."})


@app.on_event("startup")
def startup():
    init_db()


app.include_router(router, prefix="/api")
app.include_router(channel_router, prefix="/api")
app.include_router(moderation_router, prefix="/api/moderation")
app.include_router(incident_router, prefix="/api/incidents")
app.include_router(assistant_router, prefix="/api/assistant")
app.include_router(scam_router, prefix="/api/scam")
app.include_router(research_router)
app.include_router(research_router, prefix="/api/v2")
