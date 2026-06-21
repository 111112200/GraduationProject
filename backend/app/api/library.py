from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.api.deps import get_current_user
from app.services.library_service import add_to_library, remove_from_library, get_library_reports

router = APIRouter()


@router.post("/reports/{report_id}/add")
async def api_add_to_library(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok, message = add_to_library(db, report_id, current_user.id)
    if not ok:
        raise HTTPException(400, message)
    return {"success": True, "message": message}


@router.delete("/reports/{report_id}")
async def api_remove_from_library(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = remove_from_library(db, report_id, current_user.id)
    if not ok:
        raise HTTPException(404, "报告中不在底库中")
    return {"success": True}


@router.get("/reports")
async def api_get_library_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reports = get_library_reports(db, current_user.id)
    return {"reports": reports}
