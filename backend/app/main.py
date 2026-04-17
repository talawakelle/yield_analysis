from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.upload import router as upload_router
from app.api.reports import router as reports_router
from app.api.download import router as download_router
from app.core.config import settings
from app.core.paths import OUTPUTS_DIR

app = FastAPI(title="Plantation Yield Automation", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])
app.include_router(download_router, prefix="/download", tags=["download"])

app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "public_title": settings.app_public_title,
        "outputs_dir": str(OUTPUTS_DIR),
        "cors_origins": settings.cors_origins,
    }
