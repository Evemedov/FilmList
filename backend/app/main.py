"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path
from fastapi.staticfiles import StaticFiles

from app.routers import anilist, media, seasons, settings, tags, tmdb, upload
from app.services.redis import close_redis
from app.services.tmdb import close_http_client
from app.services.anilist import close_http_client as close_anilist_client
from app.config import settings as app_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown of shared async resources."""
    yield
    # Shutdown: close Redis pool and httpx clients
    await close_http_client()
    await close_anilist_client()
    await close_redis()


app = FastAPI(
    title="Personal Media Tracker",
    description="API for tracking personal media consumption (Movies, TV Shows, Anime, etc.)",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────
# Allow frontend dev server origins; tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ───────────────────────────────────────────────────
app.include_router(media.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(seasons.router, prefix="/api")
app.include_router(tmdb.router, prefix="/api")
app.include_router(anilist.router, prefix="/api")
app.include_router(upload.router, prefix="/api")

# Mount uploads directory for static file serving
upload_dir = Path(app_settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=app_settings.UPLOAD_DIR), name="uploads")


@app.get("/api/health", tags=["health"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
