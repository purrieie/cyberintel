from db.repository import ArticleRepository
from intelligence.nim_client import NIMClient
from reports.pdf_builder import build_article_pdf


class ArticleProcessor:
    def __init__(self, nim=None):
        self.repo = ArticleRepository()
        self.nim = nim

    def process_one(self, article_id: int) -> str:
        article = self.repo.get_article_by_id(article_id)
        if not article:
            raise ValueError(f"No article {article_id}")
        body = article.get("clean_text") or article.get("raw_text") or ""
        nim = self.nim or NIMClient()
        fields = nim.analyze(article["title"], article["source"], body)
        pdf_path = build_article_pdf(article, fields)
        return pdf_path
