# api/routes/articles.py
from fastapi import APIRouter, HTTPException
from db.repository import ArticleRepository

router = APIRouter()
repo = ArticleRepository()

@router.get("/")
def get_articles(limit: int = 20, offset: int = 0):
    articles = repo.get_all_articles(limit=limit, offset=offset)
    return {"count": len(articles), "articles": articles}

@router.get("/{article_id}")
def get_article(article_id: int):
    article = repo.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.get("/timeline")
def get_timeline(hours: int = 24):
    articles = repo.get_articles_by_timeframe(hours=hours)
    return {
        "timeframe_hours": hours,
        "count": len(articles),
        "articles": articles
    }