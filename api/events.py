# api/events.py
"""
Tiny in-process event bus that bridges the Scrapy crawl (running in a
background thread) to FastAPI's async SSE endpoint (running on the main
event loop).

Why this exists:
  - The storage pipeline runs inside Scrapy's thread. It cannot `await`.
  - The SSE endpoint runs on FastAPI's event loop in a different thread.
  - asyncio.Queue is not thread-safe to call across loops directly, so the
    pipeline schedules the put onto the API loop via run_coroutine_threadsafe.

Design notes:
  - Each connected browser gets its own asyncio.Queue (a subscriber).
  - publish_from_thread() fans an event out to every subscriber.
  - If no API loop is registered yet (e.g. crawl started before any client
    connected, or running the crawler standalone), publishing is a safe no-op
    so the crawl never breaks.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CrawlEventBus:
    def __init__(self) -> None:
        self._subscribers: List[asyncio.Queue] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Called once on API startup so background threads know where to post."""
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def _deliver(self, event: Dict[str, Any]) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Slow client: drop the oldest event to keep the stream live.
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    pass

    def publish_from_thread(self, event: Dict[str, Any]) -> None:
        """Safe to call from Scrapy's thread. No-op if no API loop is bound."""
        if self._loop is None:
            return
        try:
            asyncio.run_coroutine_threadsafe(self._deliver(event), self._loop)
        except Exception as e:
            logger.debug(f"Event publish skipped: {e}")

    @property
    def listener_count(self) -> int:
        return len(self._subscribers)


# Module-level singleton shared by the pipeline and the SSE route.
bus = CrawlEventBus()