import json
import trafilatura
from scrapy.http import Response
from config.seeds import SEED_SITES
from crawler.spiders.base_spider import BaseSecuritySpider
from crawler.items import ArticleItem


class KrebsOnSecuritySpider(BaseSecuritySpider):
    name = "krebsonsecurity"
    site_config = next(s for s in SEED_SITES if s.name == "krebsonsecurity")

    def parse_article(self, response: Response):
        print(f"[DEBUG] parse_article called: {response.url}")
        raw_html = response.text
        extracted = trafilatura.extract(
            raw_html,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
            output_format="json",
            with_metadata=True,
        )
        print(f"[DEBUG] extracted: {bool(extracted)}")
        if not extracted:
            return
        import json
        data = json.loads(extracted)
        print(f"[DEBUG] title: {data.get('title')}")
        item = ArticleItem(
            url=response.url,
            title=(data.get("title") or response.css("h1.entry-title::text").get("")).strip(),
            author=(data.get("author") or response.css(".author::text").get("")).strip(),
            date=(data.get("date") or response.css("time::attr(datetime)").get("")).strip(),
            source=self.site_config.name,
            raw_text=data.get("text", ""),
            categories=response.css(".cat-links a::text").getall(),
            tags=response.css(".tag-links a::text").getall(),
        )
        print(f"[DEBUG] yielding item")
        yield item