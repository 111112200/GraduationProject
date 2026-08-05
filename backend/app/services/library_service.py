from sqlalchemy.orm import Session

from app.models import Report, TextBlock, LibraryReport
from app.services.vector_store_service import (
    add_blocks_to_library,
    delete_report_from_library,
    is_report_indexed_in_library,
)
from app.services.chunk_service import build_chunks
from app.services.docx_parser_service import PARSER_VERSION
from app.services.report_service import reparse_report_if_needed


def _get_report_blocks(report: Report) -> list[dict]:
    return [
        {"report_id": report.id, "section_type": tb.section_type, "content": tb.content, "block_id": tb.id}
        for tb in report.text_blocks
    ]


def _get_report_chunks(report: Report) -> list[dict]:
    """Use the same token-aware chunks as class-internal checks."""
    return build_chunks(_get_report_blocks(report), report.id)


def _ensure_report_indexed(report: Report, user_id: int) -> bool:
    """将已登记报告补建到用户专属索引；返回是否发生了补建。"""
    if is_report_indexed_in_library(report.id, user_id):
        return False
    chunks = _get_report_chunks(report)
    if not chunks:
        return False
    add_blocks_to_library(chunks, user_id)
    return True


def ensure_user_library_index(db: Session, user_id: int):
    """为已有的底库登记按需补建用户专属向量索引。"""
    reports = db.query(Report).join(
        LibraryReport, LibraryReport.report_id == Report.id
    ).filter(
        Report.user_id == user_id
    ).all()
    for report in reports:
        upgraded = reparse_report_if_needed(db, report)
        if not upgraded or report.parser_version != PARSER_VERSION:
            continue
        _ensure_report_indexed(report, user_id)


def add_to_library(db: Session, report_id: int, user_id: int) -> tuple[bool, str]:
    """将报告加入当前用户的底库。"""
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()
    if not report:
        return False, f"报告ID {report_id} 不存在"

    upgraded = reparse_report_if_needed(db, report)
    if not upgraded or report.parser_version != PARSER_VERSION:
        return False, "报告解析版本升级失败，暂不能加入新版本底库"
    
    if report.status != "PARSED":
        return False, f"报告状态为 {report.status}，必须是 PARSED 状态才能加入底库"

    existing = db.query(LibraryReport).filter(LibraryReport.report_id == report_id).first()
    if existing:
        reindexed = _ensure_report_indexed(report, user_id)
        return True, "报告已在底库中，已补建私有索引" if reindexed else "报告已在底库中"

    chunks = _get_report_chunks(report)
    if not chunks:
        return False, "报告没有文本块(text_blocks)，无法加入底库"
    add_blocks_to_library(chunks, user_id)
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
    delete_report_from_library(report_id, user_id)
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
