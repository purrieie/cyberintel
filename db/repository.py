# db/repository.py
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.models import ENGINE, Article, Report


class ArticleRepository:

    def _session(self) -> Session:
        return Session(ENGINE)

    def url_exists(self, url_hash: str) -> bool:
        with self._session() as s:
            return s.query(Article).filter_by(url_hash=url_hash).first() is not None

    def content_exists(self, content_hash: str) -> bool:
        with self._session() as s:
            return s.query(Article).filter_by(content_hash=content_hash).first() is not None

    def insert_article(self, data: dict):
        with self._session() as s:
            article = Article(
                url=data["url"],
                url_hash=data["url_hash"],
                content_hash=data["content_hash"],
                title=data.get("title", ""),
                author=data.get("author", ""),
                date=data.get("date", ""),
                source=data["source"],
                categories=json.dumps(data.get("categories", [])),
                tags=json.dumps(data.get("tags", [])),
                raw_text=data.get("raw_text", ""),
                parse_status=data.get("parse_status", "pending"),
            )
            s.add(article)
            s.commit()

    def get_pending_articles(self, limit: int = 50):
        with self._session() as s:
            rows = (
                s.query(Article)
                .filter_by(parse_status="pending")
                .limit(limit)
                .all()
            )
            return [
                {"id": r.id, "raw_text": r.raw_text, "url": r.url}
                for r in rows
            ]

    def update_parsed(self, article_id: int, clean_text: str, parse_status: str):
        with self._session() as s:
            article = s.query(Article).filter_by(id=article_id).first()
            if article:
                article.clean_text = clean_text
                article.parse_status = parse_status
                article.parsed_at = datetime.utcnow()
                s.commit()

    def get_parsed_unsent(self, limit: int = 5):
        with self._session() as s:
            rows = (
                s.query(Article)
                .filter_by(parse_status="parsed")
                .filter(Article.groq_summary.is_(None))
                .limit(limit)
                .all()
            )
            return [self._to_dict(r) for r in rows]

    def update_grok_summary(self, article_id: int, summary: str):
        with self._session() as s:
            article = s.query(Article).filter_by(id=article_id).first()
            if article:
                article.groq_summary = summary
                s.commit()

    def get_all_articles(self, limit: int = 100, offset: int = 0):
        with self._session() as s:
            rows = s.query(Article).order_by(Article.crawled_at.desc()).offset(offset).limit(limit).all()
            return [self._to_dict(r) for r in rows]

    def get_articles_by_timeframe(self, hours: int = 24):
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        with self._session() as s:
            rows = (
                s.query(Article)
                .filter(Article.crawled_at >= cutoff)
                .order_by(Article.crawled_at.desc())
                .all()
            )
            return [self._to_dict(r) for r in rows]

    def get_article_by_id(self, article_id: int):
        with self._session() as s:
            r = s.query(Article).filter_by(id=article_id).first()
            return self._to_dict(r) if r else None

    def _to_dict(self, r: Article) -> dict:
        return {
            "id": r.id,
            "url": r.url,
            "title": r.title,
            "author": r.author,
            "date": r.date,
            "source": r.source,
            "categories": json.loads(r.categories or "[]"),
            "tags": json.loads(r.tags or "[]"),
            "raw_text": r.raw_text,
            "clean_text": r.clean_text,
            "parse_status": r.parse_status,
            "groq_summary": r.groq_summary,
            "crawled_at": str(r.crawled_at),
        }
