# api/routes/reports.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def reports_root():
    return {"message": "Reports endpoint — PDF generation coming soon"}