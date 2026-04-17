from fastapi import APIRouter, HTTPException

from app.services.data_store import get_active_report

router = APIRouter()


@router.get("/package")
def package() -> dict:
    report = get_active_report()
    if not report:
        raise HTTPException(status_code=404, detail="No generated report package found yet.")
    return report
