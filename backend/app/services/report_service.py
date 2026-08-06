import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB
from app.models import Report, TextBlock, Course, Clazz, Experiment
from app.services.docx_parser_service import PARSER_VERSION, parse_docx_report


def _extract_student_info(filename: str) -> tuple:
    """
    从文件名解析学生姓名、学号。
    支持多种格式：
      - 5120221169-任高权-作业一报告.docx       → ('任高权', '5120221169')
      - 5120221169任高权卓软2201-实验四.docx     → ('任高权', '5120221169')
      - 张三_20230001_实验1.docx               → ('张三', '20230001')
      - kmeans聚类实验.docx                     → (None, None)
    多作者时取第一个作者。
    """
    name = filename.rsplit(".", 1)[0]

    # 策略1：查找 "连续7+位数字" 紧跟 "中文姓名（2-4个汉字）" 的模式
    #   如：5120221169任高权  或  5120221169-任高权
    m = re.search(r'(\d{7,})[_\-]?([\u4e00-\u9fff]{2,4})', name)
    if m:
        return m.group(2), m.group(1)

    # 策略2：查找 "中文姓名" 后跟 "学号" 的模式
    #   如：张三_20230001  或  张三-20230001
    m = re.search(r'([\u4e00-\u9fff]{2,4})[_\-](\d{7,})', name)
    if m:
        return m.group(1), m.group(2)

    # 策略3：按分隔符拆分，尝试找到纯数字学号和中文姓名
    parts = re.split(r'[_\-]', name)
    student_id = None
    student_name = None
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if re.fullmatch(r'\d{7,}', p) and not student_id:
            student_id = p
        elif re.fullmatch(r'[\u4e00-\u9fff]{2,4}', p) and not student_name:
            student_name = p

    return student_name, student_id


def _get_user_upload_dir(user_id: int) -> Path:
    """获取用户专属上传目录"""
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


async def upload_reports(
    db: Session,
    files: List,
    experiment_id: Optional[int],
    class_id: int,
    user_id: int,
) -> dict:
    """上传报告文件，保存并解析"""
    uploaded = []
    errors = []

    # 用户专属目录：uploads/{user_id}/
    user_upload_dir = _get_user_upload_dir(user_id)

    for f in files:
        try:
            filename = f.filename or "unknown.docx"
            ext = Path(filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                errors.append({"file": filename, "error": "仅支持 .docx 格式"})
                continue

            if f.size and f.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                errors.append({"file": filename, "error": f"文件超过 {MAX_FILE_SIZE_MB}MB 限制"})
                continue

            student_name, student_id = _extract_student_info(filename)
            safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{filename}"
            file_path = user_upload_dir / safe_name

            file_bytes = await f.read()
            with open(file_path, "wb") as fp:
                fp.write(file_bytes)

            # 使用 savepoint 隔离每个文件的数据库操作，
            # 单个文件失败不会影响其他文件的提交
            savepoint = db.begin_nested()
            try:
                report = Report(
                    experiment_id=experiment_id if experiment_id else None,
                    class_id=class_id,
                    user_id=user_id,
                    student_name=student_name,
                    student_id=student_id,
                    file_name=filename,
                    file_path=str(file_path),
                    status="UPLOADED",
                )
                db.add(report)
                db.flush()

                # 解析文档
                try:
                    blocks = parse_docx_report(str(file_path))
                    for i, b in enumerate(blocks):
                        tb = TextBlock(
                            report_id=report.id,
                            section_type=b["section_type"],
                            order_index=i,
                            content=b["content"],
                            source_kind=b.get("source_kind"),
                            source_index=b.get("source_index"),
                            source_location=json.dumps(
                                b.get("source_location") or {}, ensure_ascii=False
                            ),
                            section_title=b.get("section_title"),
                            heading_level=b.get("heading_level"),
                            is_fallback=bool(b.get("fallback", False)),
                            parser_version=b.get("parser_version"),
                        )
                        db.add(tb)
                    report.status = "PARSED" if blocks else "PARSED_EMPTY"
                    report.parser_version = blocks[0].get("parser_version") if blocks else None
                    report.parse_warning = (
                        "未识别到目标章节，已使用保守全文回退；建议人工确认提取范围。"
                        if any(b.get("fallback") for b in blocks)
                        else None
                    )
                    report.parsed_at = datetime.utcnow()
                except Exception as e:
                    report.status = "FAILED"
                    report.parse_error = str(e)[:500]
                    report.parse_warning = None

                savepoint.commit()
                uploaded.append({
                    "reportId": report.id,
                    "fileName": filename,
                    "status": report.status,
                })
            except Exception as e:
                savepoint.rollback()
                # 清理已写入的文件
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except OSError:
                        pass
                errors.append({"file": filename, "error": str(e)[:200]})
        except Exception as e:
            errors.append({"file": getattr(f, "filename", "unknown"), "error": str(e)[:200]})

    # 所有文件处理完毕后统一提交外层事务
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {"success": False, "uploadedReports": [], "errors": [{"file": "batch", "error": f"数据库提交失败: {str(e)[:200]}"}]}

    return {"success": True, "uploadedReports": uploaded, "errors": errors}


def reparse_report_if_needed(db: Session, report: Report) -> bool:
    """Upgrade legacy extracted blocks before they enter a new index."""
    if report.parser_version == PARSER_VERSION:
        return True
    if report.status == "FAILED" or not report.file_path:
        return False

    try:
        blocks = parse_docx_report(report.file_path)
    except Exception as exc:
        report.parse_warning = f"新解析器升级失败，暂保留旧文本块：{str(exc)[:300]}"
        return False

    # Replace only after parsing succeeds, so a malformed file cannot erase the
    # last usable extraction.
    db.query(TextBlock).filter(TextBlock.report_id == report.id).delete(
        synchronize_session=False
    )
    for index, block in enumerate(blocks):
        db.add(
            TextBlock(
                report_id=report.id,
                section_type=block["section_type"],
                order_index=index,
                content=block["content"],
                source_kind=block.get("source_kind"),
                source_index=block.get("source_index"),
                source_location=json.dumps(
                    block.get("source_location") or {}, ensure_ascii=False
                ),
                section_title=block.get("section_title"),
                heading_level=block.get("heading_level"),
                is_fallback=bool(block.get("fallback", False)),
                parser_version=block.get("parser_version", PARSER_VERSION),
            )
        )
    report.status = "PARSED" if blocks else "PARSED_EMPTY"
    report.parser_version = PARSER_VERSION
    report.parse_warning = (
        "未识别到目标章节，已使用保守全文回退；建议人工确认提取范围。"
        if any(block.get("fallback") for block in blocks)
        else None
    )
    report.parse_error = None
    report.parsed_at = datetime.utcnow()
    db.flush()
    return True


def get_reports(
    db: Session,
    experiment_id: Optional[int] = None,
    class_id: Optional[int] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
) -> List[dict]:
    """获取报告列表"""
    from app.models import CheckResultSummary, CheckTask

    q = db.query(Report)
    if user_id:
        q = q.filter(Report.user_id == user_id)
    if experiment_id:
        q = q.filter(Report.experiment_id == experiment_id)
    if class_id:
        q = q.filter(Report.class_id == class_id)
    if status:
        q = q.filter(Report.status == status)
    reports = q.order_by(Report.id.desc()).all()

    # 批量查询所有已查重的报告 ID
    report_ids = [r.id for r in reports]
    checked_ids = set()
    if report_ids:
        checked_rows = db.query(CheckResultSummary.report_id).join(
            CheckTask, CheckTask.id == CheckResultSummary.check_task_id
        ).filter(
            CheckResultSummary.report_id.in_(report_ids),
            CheckTask.status == "COMPLETED",
        ).distinct().all()
        checked_ids = {row[0] for row in checked_rows}

    return [
        {
            "id": r.id,
            "studentName": r.student_name,
            "studentId": r.student_id,
            "fileName": r.file_name,
            "status": r.status,
            "parseWarning": r.parse_warning,
            "parserVersion": r.parser_version,
            "hasCheckResult": r.id in checked_ids,
            "experimentId": r.experiment_id,
            "classId": r.class_id,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]


def delete_report(db: Session, report_id: int, user_id: int) -> bool:
    """删除实验报告，包含数据库记录、文件以及向量库数据"""
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()
    if not report:
        return False

    # 1. 删除物理文件
    if report.file_path:
        path = Path(report.file_path)
        if path.exists():
            try:
                path.unlink()
            except Exception as e:
                print(f"Failed to delete file {path}: {e}")

    # 2. 从底库中删除向量 (如果有)
    from app.services.vector_store_service import delete_report_from_library
    try:
        delete_report_from_library(report_id, user_id)
    except Exception as e:
        print(f"Failed to delete vectors for report {report_id}: {e}")

    # 3. 删除数据库记录（包括所有关联数据）
    try:
        from app.models import TextBlock, CheckResultSummary, CheckResultDetail, LibraryReport
        from app.models.check import task_report

        # 3a. 删除 task_report 关联表中的记录（报告与查重任务的多对多关联）
        db.execute(task_report.delete().where(task_report.c.report_id == report_id))

        # 3b. 删除 library_report 底库登记记录
        db.query(LibraryReport).filter(LibraryReport.report_id == report_id).delete()

        # 3c. 删除该报告作为被比对对象（target）出现在其他报告查重结果中的记录
        db.query(CheckResultDetail).filter(CheckResultDetail.target_report_id == report_id).delete()

        # 3d. 删除该报告自身的查重结果
        summaries = db.query(CheckResultSummary).filter(CheckResultSummary.report_id == report_id).all()
        for s in summaries:
            db.query(CheckResultDetail).filter(CheckResultDetail.summary_id == s.id).delete()
        db.query(CheckResultSummary).filter(CheckResultSummary.report_id == report_id).delete()

        # 3e. 删除文本块
        db.query(TextBlock).filter(TextBlock.report_id == report_id).delete()

        # 3f. 删除报告本体
        db.delete(report)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return True


def get_report(db: Session, report_id: int, user_id: int) -> Optional[dict]:
    """获取单个报告的元数据"""
    r = db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()
    if not r:
        return None
    return {
        "id": r.id,
        "studentName": r.student_name,
        "studentId": r.student_id,
        "fileName": r.file_name,
        "status": r.status,
        "parseError": r.parse_error,
        "parseWarning": r.parse_warning,
        "parserVersion": r.parser_version,
        "experimentId": r.experiment_id,
        "classId": r.class_id,
        "createdAt": r.created_at.isoformat() if r.created_at else None,
    }
