from typing import List
from sqlalchemy.orm import Session

from app.core.config import TOP_K
from app.models import Report, TextBlock, CheckTask, CheckResultSummary, CheckResultDetail
from app.services.embedding_service import embed_texts
from app.services.chunk_service import build_chunks
from app.services.vector_store_service import (
    add_blocks_to_task,
    query_similar_task,
    query_similar_library,
    delete_task_collection,
)


def _chunk_blocks(blocks: List[dict], report_id: int) -> List[dict]:
    """Return the canonical chunks shared by all index paths."""
    return build_chunks(blocks, report_id)


def _report_blocks(report: Report) -> List[dict]:
    return [
        {
            "report_id": report.id,
            "content": tb.content,
            "section_type": tb.section_type,
            "section_title": getattr(tb, "section_title", None),
            "source_kind": getattr(tb, "source_kind", None),
            "source_location": getattr(tb, "source_location", None),
            "is_fallback": bool(getattr(tb, "is_fallback", False)),
            "block_id": tb.id,
        }
        for tb in sorted(report.text_blocks, key=lambda item: item.order_index)
    ]


def _union_length(spans: List[tuple]) -> int:
    """Calculate covered character length, without counting overlap twice."""
    grouped = {}
    for block_id, start, end in spans:
        if not isinstance(start, int) or not isinstance(end, int) or end <= start:
            continue
        grouped.setdefault(block_id, []).append((start, end))

    total = 0
    for ranges in grouped.values():
        ranges.sort()
        current_start, current_end = ranges[0]
        for start, end in ranges[1:]:
            if start <= current_end:
                current_end = max(current_end, end)
            else:
                total += current_end - current_start
                current_start, current_end = start, end
        total += current_end - current_start
    return total


def _prepare_matches(matches: List[dict], chunks: List[dict], threshold: float) -> List[dict]:
    """Deduplicate matches and attach source offsets for stable aggregation."""
    best = {}
    for match in matches:
        similarity = float(match.get("similarity", 0.0))
        if similarity < threshold:
            continue
        source_index = match.get("source_index", 0)
        if not isinstance(source_index, int) or not 0 <= source_index < len(chunks):
            continue
        source_chunk = chunks[source_index]
        enriched = dict(match)
        enriched["source_start"] = source_chunk.get("start_char")
        enriched["source_end"] = source_chunk.get("end_char")
        enriched["source_block_id"] = source_chunk.get("block_id")
        key = (
            source_index,
            match.get("target_report_id"),
            match.get("target_block_id"),
            match.get("target_start"),
            match.get("target_end"),
        )
        if key not in best or similarity > best[key].get("similarity", 0.0):
            best[key] = enriched
    return sorted(best.values(), key=lambda item: item.get("similarity", 0.0), reverse=True)


def _aggregate_score(matches: List[dict], chunks: List[dict]) -> float:
    """Score matched coverage rather than averaging duplicate overlap hits."""
    if not chunks or not matches:
        return 0.0

    total_spans = [
        (chunk.get("block_id"), chunk.get("start_char"), chunk.get("end_char"))
        for chunk in chunks
    ]
    total_length = _union_length(total_spans)
    if total_length <= 0:
        return 0.0

    best_by_source = {}
    for match in matches:
        source_index = match.get("source_index")
        if source_index not in best_by_source or match["similarity"] > best_by_source[source_index]["similarity"]:
            best_by_source[source_index] = match

    matched_spans = []
    weighted_similarity = 0.0
    weighted_length = 0
    for match in best_by_source.values():
        start = match.get("source_start")
        end = match.get("source_end")
        if not isinstance(start, int) or not isinstance(end, int) or end <= start:
            continue
        span_length = end - start
        matched_spans.append((match.get("source_block_id"), start, end))
        weighted_similarity += match["similarity"] * span_length
        weighted_length += span_length

    covered_length = _union_length(matched_spans)
    if not weighted_length or not covered_length:
        return 0.0
    quality = weighted_similarity / weighted_length
    return round(min(1.0, quality * covered_length / total_length), 4)


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
        from app.services.report_service import reparse_report_if_needed

        for report in task.reports:
            reparse_report_if_needed(db, report)

        # 1. 构建任务临时索引（仅 IN_CLASS 或 BOTH 时需要）
        if mode in ("HISTORY_ONLY", "BOTH"):
            from app.services.library_service import ensure_user_library_index
            ensure_user_library_index(db, task.user_id)

        if mode in ("IN_CLASS", "BOTH"):
            for report in task.reports:
                blocks = _report_blocks(report)
                if not blocks:
                    continue
                chunks = _chunk_blocks(blocks, report.id)
                add_blocks_to_task(chunks, task_id)

        # 2. 对每份报告执行检索并聚合结果
        for report in task.reports:
            blocks = _report_blocks(report)
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
                # Overall score measures source-text coverage, so every source
                # chunk needs its best candidate instead of one global Top-K.
                matches = query_similar_task(
                    vectors,
                    task_id,
                    TOP_K,
                    exclude_report_ids=exclude_self,
                    per_source_limit=1,
                )
                all_matches.extend(matches)

            if mode in ("HISTORY_ONLY", "BOTH"):
                lib_matches = query_similar_library(
                    vectors,
                    task.user_id,
                    TOP_K,
                    exclude_report_ids=exclude_self,
                    per_source_limit=1,
                )
                all_matches.extend(lib_matches)

            # 按相似度过滤并聚合
            valid_matches = _prepare_matches(all_matches, chunks, similar)
            overall = _aggregate_score(valid_matches, chunks)

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
                src_text = texts[src_idx] if 0 <= src_idx < len(texts) else (texts[0] if texts else "")
                source_chunk = chunks[src_idx] if 0 <= src_idx < len(chunks) else {}
                source_block_id = (
                    source_chunk.get("block_id")
                    if 0 <= src_idx < len(chunks)
                    else None
                )
                detail = CheckResultDetail(
                    summary_id=summary.id,
                    source_block_id=source_block_id,
                    target_report_id=m["target_report_id"],
                    target_block_id=m.get("target_block_id"),
                    source_text=(src_text or "")[:2000],
                    target_text=(m.get("target_text") or "")[:2000],
                    source_start=source_chunk.get("start_char"),
                    source_end=source_chunk.get("end_char"),
                    target_start=m.get("target_start"),
                    target_end=m.get("target_end"),
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
