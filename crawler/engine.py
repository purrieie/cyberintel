# crawler/engine.py
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler.spiders.bleepingcomputer import BleepingComputerSpider
from crawler.spiders.hackernews import HackerNewsSpider
from crawler.spiders.securityweek import SecurityWeekSpider
from crawler.spiders.darkreading import DarkReadingSpider
from crawler.spiders.krebsonsecurity import KrebsOnSecuritySpider

SPIDERS = [
    BleepingComputerSpider,
    HackerNewsSpider,
    SecurityWeekSpider,
    DarkReadingSpider,
    KrebsOnSecuritySpider,
]

SCRAPY_SETTINGS = {
    "USER_AGENT": "Mozilla/5.0 (compatible; CyberIntelBot/1.0)",
    "ROBOTSTXT_OBEY": True,
    "CONCURRENT_REQUESTS": 8,
    "DOWNLOAD_DELAY": 1.5,
    "DEPTH_LIMIT": 3,
    "ITEM_PIPELINES": {
        "crawler.pipelines.filter.CyberRelevanceFilterPipeline": 100,
        "crawler.pipelines.storage.DatabaseStoragePipeline": 200,
    },
    "LOG_LEVEL": "INFO",
    "HTTPCACHE_ENABLED": False,
}


def run_crawl():
    process = CrawlerProcess(settings=SCRAPY_SETTINGS)
    for spider in SPIDERS:
        process.crawl(spider)
    process.start()


if __name__ == "__main__":
    run_crawl()