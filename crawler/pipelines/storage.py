# crawler/pipelines/storage.py
import hashlib
from scrapy.exceptions import DropItem
from db.repository import ArticleRepository


class DatabaseStoragePipeline:
    def __init__(self):
        self.repo = ArticleRepository()

    def process_item(self, item, spider):
        url_hash = hashlib.sha256(item["url"].encode()).hexdigest()
        content_hash = hashlib.sha256((item.get("raw_text") or "").encode()).hexdigest()

        if self.repo.url_exists(url_hash):
            raise DropItem(f"Duplicate URL: {item['url']}")
        if self.repo.content_exists(content_hash):
            raise DropItem(f"Duplicate content: {item['url']}")

        self.repo.insert_article({
            **dict(item),
            "url_hash": url_hash,
            "content_hash": content_hash,
            "parse_status": "pending",
        })

        # Push a live event to any connected dashboard. Best-effort: a failure
        # here must never break the crawl, so it's wrapped and swallowed.
        try:
            from api.events import bus
            text = item.get("raw_text") or ""
            bus.publish_from_thread({
                "url": item["url"],
                "title": item.get("title") or "(untitled)",
                "source": item.get("source") or "unknown",
                "author": item.get("author") or "",
                "date": item.get("date") or "",
                "preview": text[:240],
                "word_count": len(text.split()),
            })
        except Exception:
            pass

        return item