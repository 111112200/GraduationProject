from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.report_service import upload_reports, get_reports, delete_report, get_report
from app.services.chunk_service import calculate_report_chunks
from app.models import Report

router = APIRouter()


@router.post("/upload")
async def api_upload_reports(
    files: List[UploadFile] = File(...),
    experimentId: Optional[int] = Form(None),
    classId: int = Form(...),
    db: Session = Depends(get_db),
):
    result = await upload_reports(db, files, experimentId, classId)
    return result


@router.get("")
async def api_get_reports(
    experimentId: Optional[int] = None,
    classId: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    reports = get_reports(db, experimentId, classId, status)
    return {"reports": reports}


@router.get("/{report_id}/result")
async def api_get_report_result(
    report_id: int,
    db: Session = Depends(get_db),
):
    from app.models import CheckResultSummary, CheckResultDetail, Report
    summary = db.query(CheckResultSummary).filter(
        CheckResultSummary.report_id == report_id
    ).order_by(CheckResultSummary.created_at.desc()).first()
    if not summary:
        report = db.query(Report).filter(Report.id == report_id).first()
        return {
            "reportId": report_id,
            "hasCheckResult": False,
            "overallScore": 0,
            "riskLevel": "LOW",
            "segments": [],
        }
    details = db.query(CheckResultDetail).filter(
        CheckResultDetail.summary_id == summary.id
    ).all()
    report = db.query(Report).filter(Report.id == report_id).first()
    target_reports = {}
    for d in details:
        if d.target_report_id not in target_reports:
            tr = db.query(Report).filter(Report.id == d.target_report_id).first()
            target_reports[d.target_report_id] = tr.student_name if tr else ""
    segments = [
        {
            "sourceBlockId": d.source_block_id,
            "sourceText": d.source_text,
            "targetReportId": d.target_report_id,
            "targetStudentName": target_reports.get(d.target_report_id, ""),
            "targetBlockId": d.target_block_id,
            "targetText": d.target_text,
            "similarity": d.similarity,
            "mode": d.mode,
        }
        for d in details
    ]
    return {
        "reportId": report_id,
        "hasCheckResult": True,
        "overallScore": summary.overall_score,
        "riskLevel": summary.risk_level,
        "segments": segments,
    }

@router.get("/{report_id}/chunks")
async def api_get_report_chunks(
    report_id: int,
    db: Session = Depends(get_db),
):
    """返回报告的向量分块详情，用于可视化预处理效果"""
    result = calculate_report_chunks(db, report_id)
    if result is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    return result


@router.get("/{report_id}")
async def api_get_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    report = get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report

@router.delete("/{report_id}")
async def api_delete_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    success = delete_report(db, report_id)
    if not success:
        raise HTTPException(status_code=404, detail="报告不存在")
    return {"success": True}
