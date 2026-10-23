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
    allow_origins=settings.cors_origin_list + ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
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
