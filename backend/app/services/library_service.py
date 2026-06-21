from sqlalchemy.orm import Session

from app.models import Report, TextBlock, LibraryReport
from app.services.vector_store_service import add_blocks_to_library, delete_report_from_library


def add_to_library(db: Session, report_id: int, user_id: int) -> tuple[bool, str]:
    """将报告加入底库"""
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()
    if not report:
        return False, f"报告ID {report_id} 不存在"
    
    if report.status != "PARSED":
        return False, f"报告状态为 {report.status}，必须是 PARSED 状态才能加入底库"

    existing = db.query(LibraryReport).filter(LibraryReport.report_id == report_id).first()
    if existing:
        return True, "报告已在底库中"

    blocks = [
        {"report_id": report.id, "section_type": tb.section_type, "content": tb.content, "block_id": tb.id}
        for tb in report.text_blocks
    ]
    if not blocks:
        return False, "报告没有文本块(text_blocks)，无法加入底库"

    add_blocks_to_library(blocks)
    lib = LibraryReport(report_id=report_id)
    db.add(lib)
    db.commit()
    return True, "成功加入底库"


def remove_from_library(db: Session, report_id: int, user_id: int) -> bool:
    """从底库移除报告"""
    lib = db.query(LibraryReport).join(Report, LibraryReport.report_id == Report.id).filter(
        LibraryReport.report_id == report_id, Report.user_id == user_id
    ).first()
    if not lib:
        return False
    delete_report_from_library(report_id)
    db.delete(lib)
    db.commit()
    return True


def get_library_reports(db: Session, user_id: int) -> list:
    """获取底库报告列表"""
    from app.models import Report
    items = db.query(LibraryReport, Report).join(Report, LibraryReport.report_id == Report.id).filter(
        Report.user_id == user_id
    ).all()
    return [
        {
            "reportId": r.id,
            "studentName": r.student_name,
            "studentId": r.student_id,
            "fileName": r.file_name,
        }
        for _, r in items
    ]
