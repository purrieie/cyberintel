# crawler/items.py
import scrapy

class ArticleItem(scrapy.Item):
    url        = scrapy.Field()
    title      = scrapy.Field()
    author     = scrapy.Field()
    date       = scrapy.Field()
    source     = scrapy.Field()
    raw_text   = scrapy.Field()
    categories = scrapy.Field()
    tags       = scrapy.Field()