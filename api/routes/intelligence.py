# api/routes/intelligence.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def intelligence_root():
    return {"message": "Intelligence endpoint — Grok integration coming soon"}