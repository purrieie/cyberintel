# api/routes/reports.py
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from intelligence.article_processor import ArticleProcessor

router = APIRouter()
processor = ArticleProcessor()


@router.post("/generate/{article_id}")
def generate_report(article_id: int):
    try:
        path = processor.process_one(article_id)
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=path.split("/")[-1],
        )
    except Exception as e:
        traceback.print_exc()   # full traceback to terminal
        print(f"[REPORT ERROR] article_id={article_id}: {e!r}")
        raise HTTPException(status_code=500, detail=str(e))