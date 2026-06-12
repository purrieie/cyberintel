# api/main.py
from fastapi import FastAPI
from api.routes import articles, crawler, intelligence, reports

app = FastAPI(
    title="CyberIntel API",
    description="Cybersecurity Intelligence Crawler API",
    version="1.0.0",
)

app.include_router(articles.router, prefix="/articles", tags=["Articles"])
app.include_router(crawler.router, prefix="/crawl", tags=["Crawler"])
app.include_router(intelligence.router, prefix="/intelligence", tags=["Intelligence"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

@app.get("/")
def root():
    return {"status": "ok", "message": "CyberIntel is running"}