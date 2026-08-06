from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.report_service import upload_reports, get_reports, delete_report, get_report
from app.services.chunk_service import calculate_report_chunks
from app.models import Clazz, Experiment, Report, User
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/upload")
async def api_upload_reports(
    files: List[UploadFile] = File(...),
    experimentId: Optional[int] = Form(None),
    classId: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clazz = db.query(Clazz).filter(
        Clazz.id == classId,
        Clazz.user_id == current_user.id,
    ).first()
    if not clazz:
        raise HTTPException(status_code=404, detail="班级不存在或无权使用")

    if experimentId is not None:
        experiment = db.query(Experiment).filter(
            Experiment.id == experimentId,
            Experiment.user_id == current_user.id,
        ).first()
        if not experiment:
            raise HTTPException(status_code=404, detail="实验不存在或无权使用")

    result = await upload_reports(db, files, experimentId, classId, current_user.id)
    return result


@router.get("")
async def api_get_reports(
    experimentId: Optional[int] = None,
    classId: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reports = get_reports(db, experimentId, classId, status, current_user.id)
    return {"reports": reports}


@router.get("/{report_id}/result")
async def api_get_report_result(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models import CheckResultSummary, CheckResultDetail, CheckTask, Report
    
    # Verify report belongs to user
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    summary = db.query(CheckResultSummary).filter(
        CheckResultSummary.report_id == report_id
    ).join(
        CheckTask, CheckTask.id == CheckResultSummary.check_task_id
    ).filter(
        CheckTask.status == "COMPLETED"
    ).order_by(CheckResultSummary.created_at.desc()).first()
    if not summary:
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
    target_report_ids = {d.target_report_id for d in details}
    target_reports = {}
    if target_report_ids:
        target_reports = {
            r.id: r.student_name
            for r in db.query(Report).filter(
                Report.id.in_(target_report_ids),
                Report.user_id == current_user.id,
            ).all()
        }
    segments = [
        {
            "sourceBlockId": d.source_block_id,
            "sourceStart": getattr(d, "source_start", None),
            "sourceEnd": getattr(d, "source_end", None),
            "sourceText": d.source_text,
            "targetReportId": d.target_report_id,
            "targetStudentName": target_reports.get(d.target_report_id, ""),
            "targetBlockId": d.target_block_id,
            "targetStart": getattr(d, "target_start", None),
            "targetEnd": getattr(d, "target_end", None),
            "targetText": d.target_text,
            "similarity": d.similarity,
            "mode": d.mode,
        }
        for d in details
        if d.target_report_id in target_reports
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
    current_user: User = Depends(get_current_user),
):
    """返回报告的向量分块详情，用于可视化预处理效果"""
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    from app.services.docx_parser_service import PARSER_VERSION
    from app.services.report_service import reparse_report_if_needed
    was_current = report.parser_version == PARSER_VERSION
    if reparse_report_if_needed(db, report) and not was_current:
        db.commit()
        
    result = calculate_report_chunks(db, report_id)
    if result is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    return result


@router.get("/{report_id}")
async def api_get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report

@router.delete("/{report_id}")
async def api_delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = delete_report(db, report_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="报告不存在")
    return {"success": True}
