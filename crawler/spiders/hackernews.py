import json
import trafilatura
from scrapy.http import Response
from config.seeds import SEED_SITES
from crawler.spiders.base_spider import BaseSecuritySpider
from crawler.items import ArticleItem


class HackerNewsSpider(BaseSecuritySpider):
    name = "thehackernews"
    site_config = next(s for s in SEED_SITES if s.name == "thehackernews")

    def parse_article(self, response: Response):
        raw_html = response.text
        extracted = trafilatura.extract(raw_html, include_comments=False,
            include_tables=False, favor_precision=True,
            output_format="json", with_metadata=True)
        if not extracted:
            return
        data = json.loads(extracted)
        yield ArticleItem(
            url=response.url,
            title=(data.get("title") or response.css("h1.story-title::text").get("")).strip(),
            author=(data.get("author") or "").strip(),
            date=(data.get("date") or response.css("span.author span::text").get("")).strip(),
            source=self.site_config.name,
            raw_text=data.get("text", ""),
            categories=response.css(".label::text").getall(),
            tags=[],
        )