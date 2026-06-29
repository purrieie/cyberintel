import hashlib

from scrapy.exceptions import DropItem

from db.repository import ArticleRepository
from intelligence.relevance_agent import RelevanceAgent
from parser.date_filter import MAX_AGE_DAYS as MAX_ARTICLE_AGE_DAYS
from parser.date_filter import is_recent

BATCH_SIZE = 15


class BatchRelevanceStoragePipeline:
    """
    Terminal pipeline. Buffers items, judges them in batches via the AI agent,
    and stores ONLY the keepers. Nothing runs after this in the chain.
    """

    def __init__(self):
        self.repo = ArticleRepository()
        self.agent = RelevanceAgent()
        self.buffer = []

    def process_item(self, item, spider):
        if not is_recent(item.get("date"), item.get("url", "")):
            raise DropItem(f"older than {MAX_ARTICLE_AGE_DAYS}d: {item.get('url')}")

        self.buffer.append(item)
        print(f"[DEBUG] buffered {len(self.buffer)}/{BATCH_SIZE}")
        if len(self.buffer) >= BATCH_SIZE:
            print("[DEBUG] flushing batch...")
            self._flush(spider)
        return item

    def close_spider(self, spider):
        self._flush(spider)

    def _flush(self, spider):
        if not self.buffer:
            return
        batch = self.buffer
        self.buffer = []

        try:
            kept = self.agent.judge_batch([dict(item) for item in batch])
            print(f"[DEBUG] judged {len(batch)} -> kept {len(kept)}")
        except Exception as e:
            print(f"[DEBUG] judge FAILED: {e!r}")
            kept = [dict(item, severity=item.get("severity", "medium")) for item in batch]

        stored = 0
        dupes = 0
        for item in kept:
            if not isinstance(item, dict) or not item.get("url"):
                print(f"[DEBUG] skipping kept item with no url")
                continue
            item.setdefault("severity", "low")
            try:
                if self._store(item, spider):
                    stored += 1
                else:
                    dupes += 1
            except Exception as e:
                import traceback
                print(f"[DEBUG] flush-loop error for {item.get('url')}: {e!r}")
                traceback.print_exc()
        print(f"[DEBUG] flush done: stored={stored} duplicates_skipped={dupes}")

    def _store(self, item, spider) -> bool:
        """Returns True if a new article was stored, False if it was a duplicate."""
        url_hash = hashlib.sha256(item["url"].encode()).hexdigest()
        content_hash = hashlib.sha256((item.get("raw_text") or "").encode()).hexdigest()

        try:
            if self.repo.url_exists(url_hash):
                print(f"[DEBUG] DUP url: {item['url']}")
                return False
            if self.repo.content_exists(content_hash):
                print(f"[DEBUG] DUP content: {item['url']}")
                return False

            new_id = self.repo.insert_article({
                **dict(item),
                "url_hash": url_hash,
                "content_hash": content_hash,
                "parse_status": "pending",
            })
            print(f"[DEBUG] STORED id={new_id}: {item.get('title')}")
        except Exception as e:
            import traceback
            print(f"[DEBUG] STORE FAILED for {item.get('url')}: {e!r}")
            traceback.print_exc()
            return False

        try:
            from api.events import bus
            text = item.get("raw_text") or ""
            listeners = getattr(bus, "listener_count", "?")
            bus.publish_from_thread({
                "url": item["url"],
                "title": item.get("title") or "(untitled)",
                "source": item.get("source") or "unknown",
                "author": item.get("author") or "",
                "date": item.get("date") or "",
                "preview": text[:240],
                "word_count": len(text.split()),
                "severity": item.get("severity", "low"),
                "id": new_id,
            })
            print(f"[DEBUG] published (listeners={listeners})")
        except Exception as e:
            import traceback
            print(f"[DEBUG] publish FAILED: {e!r}")
            traceback.print_exc()

        return True