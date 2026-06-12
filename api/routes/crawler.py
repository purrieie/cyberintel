# api/routes/crawler.py
import threading
from fastapi import APIRouter
from crawler.engine import run_crawl

router = APIRouter()
crawl_status = {"running": False, "message": "idle"}

@router.post("/start")
def start_crawl():
    if crawl_status["running"]:
        return {"status": "already running"}

    def _run():
        crawl_status["running"] = True
        crawl_status["message"] = "crawling..."
        try:
            run_crawl()
            crawl_status["message"] = "completed"
        except Exception as e:
            crawl_status["message"] = f"error: {e}"
        finally:
            crawl_status["running"] = False

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"status": "started"}

@router.get("/status")
def get_status():
    return crawl_status