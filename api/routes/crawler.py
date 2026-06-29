# api/routes/crawler.py
import asyncio
import json
import threading

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from twisted.internet import reactor

from crawler.engine import run_crawl
from api.events import bus

router = APIRouter()
crawl_status = {"running": False, "message": "idle"}
_active = {"process": None}


@router.post("/start")
def start_crawl():
    if crawl_status["running"]:
        return {"status": "already running"}

    def _run():
        crawl_status["running"] = True
        crawl_status["message"] = "crawling..."
        bus.publish_from_thread({"_event": "status", "running": True, "message": "crawling..."})
        try:
            run_crawl(on_start=lambda p: _active.__setitem__("process", p))
            crawl_status["message"] = "completed"
        except Exception as e:
            crawl_status["message"] = f"error: {e}"
        finally:
            crawl_status["running"] = False
            _active["process"] = None
            bus.publish_from_thread({
                "_event": "status",
                "running": False,
                "message": crawl_status["message"],
            })

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"status": "started"}


@router.post("/stop")
def stop_crawl():
    if not crawl_status["running"]:
        return {"status": "not running"}
    crawl_status["message"] = "stopping..."
    bus.publish_from_thread({"_event": "status", "running": True, "message": "stopping..."})
    try:
        reactor.callFromThread(reactor.stop)
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {"status": "stopping"}


@router.get("/status")
def get_status():
    return {**crawl_status, "listeners": bus.listener_count}


@router.get("/stream")
async def stream(request: Request):
    """
    Server-Sent Events stream of articles as they're crawled.
    Each new article arrives as a JSON `data:` line. A periodic comment
    keepalive holds the connection open through idle gaps and proxies.
    """
    queue = bus.subscribe()

    async def event_generator():
        try:
            yield f"event: hello\ndata: {json.dumps({'listeners': bus.listener_count})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue

                name = event.pop("_event", "article")
                yield f"event: {name}\ndata: {json.dumps(event)}\n\n"
        finally:
            bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
