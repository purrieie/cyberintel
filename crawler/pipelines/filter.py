# crawler/pipelines/filter.py
class CyberRelevanceFilterPipeline:
    def process_item(self, item, spider):
        # No filtering — these are dedicated cybersecurity sites
        text = (item.get("raw_text") or "").lower()
        if len(text) < 50:  # sirf empty pages drop karo
            from scrapy.exceptions import DropItem
            raise DropItem(f"Empty article: {item['url']}")
        return item