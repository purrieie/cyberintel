# parser/pipeline.py
"""
Orchestrates all three parser stages.
Reads 'pending' articles from DB, processes them,
writes clean_text back, marks as 'parsed'.
"""
import logging
from db.repository import ArticleRepository
from parser.cleaner import TextCleaner
from parser.normalizer import TextNormalizer
from parser.deduplicator import ParagraphDeduplicator

logger = logging.getLogger(__name__)


class ParserPipeline:
    def __init__(self):
        self.repo = ArticleRepository()
        self.cleaner = TextCleaner()
        self.normalizer = TextNormalizer()
        self.deduplicator = ParagraphDeduplicator()

    def process_pending(self, batch_size: int = 50):
        articles = self.repo.get_pending_articles(limit=batch_size)
        logger.info(f"Processing {len(articles)} pending articles")

        for article in articles:
            try:
                clean_text = self._process(article["raw_text"])
                self.repo.update_parsed(
                    article_id=article["id"],
                    clean_text=clean_text,
                    parse_status="parsed",
                )
            except Exception as e:
                logger.error(f"Parser failed for article {article['id']}: {e}")
                self.repo.update_parsed(
                    article_id=article["id"],
                    clean_text="",
                    parse_status="parse_error",
                )

    def _process(self, raw_text: str) -> str:
        text = self.cleaner.clean(raw_text)
        text = self.normalizer.normalize(text)
        text = self.deduplicator.deduplicate(text)
        return text