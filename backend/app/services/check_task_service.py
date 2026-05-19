from typing import List
from sqlalchemy.orm import Session

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP, TOP_K
from app.models import Report, TextBlock, CheckTask, CheckResultSummary, CheckResultDetail, LibraryReport
from app.services.embedding_service import embed_texts
from app.services.vector_store_service import (
    add_blocks_to_task,
    add_blocks_to_library,
    query_similar_task,
    query_similar_library,
    delete_task_collection,
)
from app.services.docx_parser_service import parse_docx_report


def _chunk_blocks(blocks: List[dict], report_id: int) -> List[dict]:
    """对文本块进行分块"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "。", "！", "？", "\n"],
        length_function=len,
    )
    chunks = []
    for i, b in enumerate(blocks):
        for chunk in splitter.split_text(b.get("content", "")):
            # 去除分块后可能遗留在开头的标点符号和空白字符
            chunk = chunk.lstrip("。！？\n\r\t ")
            if len(chunk.strip()) >= 10:
                chunks.append({
                    "report_id": report_id,
                    "section_type": b.get("section_type", ""),
                    "content": chunk,
                    "block_id": i,
                })
    return chunks


def _calc_risk_level(overall_score: float, high: float, similar: float) -> str:
    if overall_score >= high:
        return "HIGH"
    if overall_score >= similar:
        return "MEDIUM"
    return "LOW"


def execute_check_task(db: Session, task_id: int):
    """执行查重任务"""
    task = db.query(CheckTask).filter(CheckTask.id == task_id).first()
    if not task or task.status != "PENDING":
        return

    task.status = "RUNNING"
    db.commit()

    report_ids = [r.id for r in task.reports]
    if not report_ids:
        task.status = "COMPLETED"
        db.commit()
        return

    high = task.high_risk_threshold
    similar = task.similar_threshold
    mode = task.mode

    try:
        # 1. 构建任务临时索引（仅 IN_CLASS 或 BOTH 时需要）
        if mode in ("IN_CLASS", "BOTH"):
            for report in task.reports:
                blocks = [{"content": tb.content, "section_type": tb.section_type} for tb in report.text_blocks]
                if not blocks:
                    continue
                chunks = _chunk_blocks(blocks, report.id)
                chunk_with_ids = []
                for c in chunks:
                    chunk_with_ids.append({
                        **c,
                        "block_id": c.get("block_id"),
                    })
                add_blocks_to_task(chunk_with_ids, task_id)

        # 2. 对每份报告执行检索并聚合结果
        for report in task.reports:
            blocks = [{"content": tb.content, "section_type": tb.section_type} for tb in report.text_blocks]
            if not blocks:
                summary = CheckResultSummary(
                    check_task_id=task_id,
                    report_id=report.id,
                    overall_score=0.0,
                    risk_level="LOW",
                )
                db.add(summary)
                continue

            chunks = _chunk_blocks(blocks, report.id)
            if not chunks:
                summary = CheckResultSummary(
                    check_task_id=task_id,
                    report_id=report.id,
                    overall_score=0.0,
                    risk_level="LOW",
                )
                db.add(summary)
                continue

            texts = [c["content"] for c in chunks]
            vectors = embed_texts(texts)
            exclude_self = {report.id}

            all_matches = []

            if mode in ("IN_CLASS", "BOTH"):
                matches = query_similar_task(vectors, task_id, TOP_K, exclude_report_ids=exclude_self)
                all_matches.extend(matches)

            if mode in ("HISTORY_ONLY", "BOTH"):
                lib_matches = query_similar_library(vectors, TOP_K)
                all_matches.extend(lib_matches)

            # 按相似度过滤并聚合
            valid_matches = [m for m in all_matches if m["similarity"] >= similar]
            if not valid_matches:
                overall = 0.0
            else:
                overall = sum(m["similarity"] for m in valid_matches) / len(valid_matches)
                overall = min(1.0, overall)

            risk = _calc_risk_level(overall, high, similar)
            summary = CheckResultSummary(
                check_task_id=task_id,
                report_id=report.id,
                overall_score=round(overall, 4),
                risk_level=risk,
            )
            db.add(summary)
            db.flush()

            for m in valid_matches[:20]:
                src_idx = m.get("source_index", 0)
                src_text = texts[src_idx] if src_idx < len(texts) else (texts[0] if texts else "")
                detail = CheckResultDetail(
                    summary_id=summary.id,
                    source_block_id=None,
                    target_report_id=m["target_report_id"],
                    target_block_id=m.get("target_block_id"),
                    source_text=(src_text or "")[:2000],
                    target_text=(m.get("target_text") or "")[:2000],
                    similarity=m["similarity"],
                    mode=m.get("mode", "IN_CLASS"),
                )
                db.add(detail)

        task.status = "COMPLETED"
        delete_task_collection(task_id)
    except Exception as e:
        task.status = "FAILED"
        delete_task_collection(task_id)
        raise
    finally:
        db.commit()
