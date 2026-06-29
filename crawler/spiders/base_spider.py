# crawler/spiders/base_spider.py
import hashlib
import re
import logging
from typing import Generator
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.http import Response

from config.seeds import SiteConfig
from db.repository import ArticleRepository

logging.getLogger("trafilatura").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

CYBER_KEYWORDS = [
    "cve", "vulnerability", "malware", "ransomware", "threat actor",
    "apt", "data breach", "exploit", "zero-day", "zero day",
    "security advisory", "patch", "backdoor", "trojan", "botnet",
    "phishing", "credential", "remote code execution", "rce",
    "privilege escalation", "supply chain", "incident response",
]

DENY_KEYWORDS = [
    "advertise", "login", "signin", "register", "contact",
    "privacy-policy", "terms-of-service", "careers", "about-us",
]


class BaseSecuritySpider(scrapy.Spider):

    site_config: SiteConfig = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo = ArticleRepository()
        self._visited_urls: set = set()

    @property
    def start_urls(self):
        return self.site_config.seed_urls

    @property
    def allowed_domains(self):
        return self.site_config.allowed_domains

    def _is_article_url(self, url: str) -> bool:
        return any(
            re.search(pat, urlparse(url).path)
            for pat in self.site_config.article_path_patterns
        )

    def _is_category_url(self, url: str) -> bool:
        return any(
            re.search(pat, urlparse(url).path)
            for pat in self.site_config.category_path_patterns
        )

    def _is_denied_url(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        if any(re.search(pat, path) for pat in self.site_config.deny_patterns):
            return True
        if any(kw in path for kw in DENY_KEYWORDS):
            return True
        return False

    def _url_hash(self, url: str) -> str:
        return hashlib.sha256(url.strip().encode()).hexdigest()

    def _already_crawled(self, url: str) -> bool:
        url_hash = self._url_hash(url)
        # Sirf DB check karo, in-memory set nahi
        return self.repo.url_exists(url_hash)

    def _cyber_relevance_score(self, text: str) -> int:
        text_lower = text.lower()
        return sum(1 for kw in CYBER_KEYWORDS if kw in text_lower)

    def _is_relevant(self, response: Response) -> bool:
        title = response.css("title::text").get(default="")
        meta_desc = response.css('meta[name="description"]::attr(content)').get(default="")
        body_preview = " ".join(response.css("p::text").getall()[:10])
        combined = f"{title} {meta_desc} {body_preview}"
        return self._cyber_relevance_score(combined) >= 2

    def parse(self, response: Response) -> Generator:
        # Skip non-HTML responses (images, PDFs, etc.)
        content_type = response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore")
        if not any(t in content_type for t in ["text/html", "application/xhtml"]):
            return

        current_url = response.url

        if self._is_denied_url(current_url):
            return

        if self._is_article_url(current_url):
            if not self._already_crawled(current_url):
                yield from self.parse_article(response)
        elif self._is_category_url(current_url):
            yield from self.parse_category(response)

        yield from self._follow_links(response)

    def _follow_links(self, response: Response) -> Generator:
        # Skip non-HTML
        content_type = response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore")
        if not any(t in content_type for t in ["text/html", "application/xhtml"]):
            return

        for href in response.css("a::attr(href)").getall():
            # Skip non-http schemes
            if any(href.startswith(p) for p in ["mailto:", "javascript:", "tel:", "#"]):
                continue

            url = urljoin(response.url, href)

            if not url.startswith("http"):
                continue

            if not any(domain in url for domain in self.site_config.allowed_domains):
                continue

            if self._is_denied_url(url):
                continue

            if "replytocom" in url or "comment-" in url:
                continue

            url_hash = self._url_hash(url)
            if url_hash in self._visited_urls:
                continue

            self._visited_urls.add(url_hash)

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self._handle_error,
                meta={"depth": response.meta.get("depth", 0) + 1},
                dont_filter=False,
            )

    def parse_category(self, response: Response) -> Generator:
        for next_page in response.css(
            'a[rel="next"]::attr(href), .pagination a::attr(href)'
        ).getall():
            url = urljoin(response.url, next_page)
            yield scrapy.Request(url, callback=self.parse, errback=self._handle_error)

    def parse_article(self, response: Response) -> Generator:
        raise NotImplementedError

    def _handle_error(self, failure):
        logger.error(f"[ERROR] {failure.request.url} — {failure.value}")
