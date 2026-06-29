# api/main.py
import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from api.routes import articles, crawler, intelligence, reports
from api.events import bus

app = FastAPI(
    title="CyberIntel API",
    description="Cybersecurity Intelligence Crawler API",
    version="1.0.0",
)

app.include_router(articles.router, prefix="/articles", tags=["Articles"])
app.include_router(crawler.router, prefix="/crawl", tags=["Crawler"])
app.include_router(intelligence.router, prefix="/intelligence", tags=["Intelligence"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

STATIC_DIR = Path(__file__).parent / "static"


@app.on_event("startup")
async def _startup():
    # Create DB tables if they don't exist yet (safe to call every boot).
    from db.models import init_db
    init_db()
    # Give the cross-thread event bus a handle to this loop so the crawler
    # (running in a background thread) can push live events to SSE clients.
    bus.bind_loop(asyncio.get_running_loop())

@app.get("/")
def root():
    return {"status": "ok", "message": "CyberIntel is running"}


@app.get("/dashboard")
def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html")