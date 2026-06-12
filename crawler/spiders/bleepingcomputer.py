# crawler/spiders/bleepingcomputer.py
import trafilatura
from scrapy.http import Response

from config.seeds import SEED_SITES
from crawler.spiders.base_spider import BaseSecuritySpider
from crawler.items import ArticleItem


class BleepingComputerSpider(BaseSecuritySpider):
    name = "bleepingcomputer"
    site_config = next(s for s in SEED_SITES if s.name == "bleepingcomputer")

    def parse_article(self, response: Response):
        # Trafilatura does the heavy lifting
        raw_html = response.text
        extracted = trafilatura.extract(
            raw_html,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
            output_format="json",
            with_metadata=True,
        )

        if not extracted:
            return

        import json
        data = json.loads(extracted)

        # Fallback selectors for metadata Trafilatura might miss
        title = (
            data.get("title")
            or response.css("h1.article_title::text").get("")
            or response.css("h1::text").get("")
        ).strip()

        author = (
            data.get("author")
            or response.css(".article_author a::text").get("")
        ).strip()

        date = (
            data.get("date")
            or response.css("time::attr(datetime)").get("")
        ).strip()

        categories = response.css(".bc_tag_area a::text").getall()
        tags = response.css(".tags a::text").getall()

        yield ArticleItem(
            url=response.url,
            title=title,
            author=author,
            date=date,
            source=self.site_config.name,
            raw_text=data.get("text", ""),
            categories=categories,
            tags=tags,
        )