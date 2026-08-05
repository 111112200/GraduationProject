import re
from typing import Callable, List, Optional

from sqlalchemy.orm import Session

from app.core.config import CHUNK_OVERLAP, CHUNK_SIZE, CHUNK_VERSION
from app.models import Report
from app.services.embedding_service import count_embedding_tokens


LengthFunction = Callable[[str], int]
MIN_CHUNK_CHARS = 5
_BOUNDARY_RE = re.compile(r"[。！？!?；;\n]+")


def _find_overlap(text_a: str, text_b: str, max_len: int) -> str:
    """Return the actual suffix/prefix overlap for backwards-compatible UI data."""
    if not text_a or not text_b or max_len <= 0:
        return ""
    candidate = text_b[:max_len]
    for length in range(len(candidate), 0, -1):
        if text_a.endswith(candidate[:length]):
            return candidate[:length]
    return ""


def _max_end(text: str, start: int, max_tokens: int, length_function: LengthFunction) -> int:
    """Find the furthest character offset that fits the token budget."""
    if start >= len(text):
        return start
    if length_function(text[start:]) <= max_tokens:
        return len(text)

    low = start + 1
    high = len(text)
    best = start + 1
    while low <= high:
        middle = (low + high) // 2
        if length_function(text[start:middle]) <= max_tokens:
            best = middle
            low = middle + 1
        else:
            high = middle - 1
    return best


def _preferred_end(text: str, start: int, candidate_end: int) -> int:
    """Prefer a sentence boundary without producing tiny fragments."""
    boundaries = [m.end() for m in _BOUNDARY_RE.finditer(text, start, candidate_end)]
    usable = [b for b in boundaries if b - start >= MIN_CHUNK_CHARS]
    return max(usable) if usable else candidate_end


def _overlap_start(
    text: str,
    start: int,
    end: int,
    overlap_tokens: int,
    length_function: LengthFunction,
) -> int:
    if overlap_tokens <= 0:
        return end

    # Find the longest suffix no larger than the overlap budget. Token length
    # is monotonic enough for binary search for the supported tokenizers.
    low, high = start, end
    best = end
    while low <= high:
        middle = (low + high) // 2
        if length_function(text[middle:end]) <= overlap_tokens:
            best = middle
            high = middle - 1
        else:
            low = middle + 1

    # If possible, start the overlap at a sentence boundary at or after the
    # calculated position. This avoids carrying a dangling punctuation mark.
    boundaries = [m.end() for m in _BOUNDARY_RE.finditer(text, best, end) if m.end() < end]
    if boundaries:
        return min(boundaries)
    return best


def split_text_with_offsets(
    text: str,
    max_tokens: int = CHUNK_SIZE,
    overlap_tokens: int = CHUNK_OVERLAP,
    length_function: LengthFunction = count_embedding_tokens,
) -> List[dict]:
    """Split text by sentence boundaries and return stable character offsets."""
    if not text or not text.strip():
        return []
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be in [0, max_tokens)")

    chunks: List[dict] = []
    start = 0
    while start < len(text):
        candidate_end = _max_end(text, start, max_tokens, length_function)
        if candidate_end <= start:
            candidate_end = min(len(text), start + 1)
        end = (
            _preferred_end(text, start, candidate_end)
            if candidate_end < len(text)
            else candidate_end
        )
        if (
            end < len(text)
            and length_function(text[start:end]) <= overlap_tokens
        ):
            end = candidate_end
        if end <= start:
            end = candidate_end

        piece = text[start:end]
        if piece.strip() and len(piece.strip()) >= MIN_CHUNK_CHARS:
            chunks.append(
                {
                    "content": piece,
                    "start_char": start,
                    "end_char": end,
                    "token_length": length_function(piece),
                }
            )

        if end >= len(text):
            break
        next_start = _overlap_start(text, start, end, overlap_tokens, length_function)
        if next_start <= start:
            next_start = start + 1
        start = next_start
    return chunks


def build_chunks(blocks: List[dict], report_id: Optional[int] = None) -> List[dict]:
    """Build the canonical chunks used by indexing, querying, and preview."""
    chunks: List[dict] = []
    for block_index, block in enumerate(blocks):
        content = block.get("content") or ""
        if not content.strip():
            continue
        block_id = block.get("block_id")
        effective_report_id = report_id if report_id is not None else block.get("report_id")
        pieces = split_text_with_offsets(content)
        for piece_index, piece in enumerate(pieces):
            stable_block_id = block_id if block_id is not None else f"p{block_index}"
            stable_report_id = effective_report_id if effective_report_id is not None else "unknown"
            chunks.append(
                {
                    "chunk_id": f"r{stable_report_id}_b{stable_block_id}_c{piece_index}",
                    "report_id": effective_report_id,
                    "section_type": block.get("section_type") or "GENERAL",
                    "section_title": block.get("section_title"),
                    "block_id": block_id,
                    "source_kind": block.get("source_kind"),
                    "source_location": block.get("source_location"),
                    "is_fallback": bool(block.get("is_fallback", block.get("fallback", False))),
                    "content": piece["content"],
                    "start_char": piece["start_char"],
                    "end_char": piece["end_char"],
                    "token_length": piece["token_length"],
                    "chunk_version": CHUNK_VERSION,
                }
            )
    return chunks


def _overlap_for_pair(previous: dict, current: dict) -> tuple[str, str]:
    """Return overlap labels only for chunks from the same source block."""
    if previous.get("block_id") != current.get("block_id"):
        return "", ""
    previous_end = previous.get("end_char")
    current_start = current.get("start_char")
    if not isinstance(previous_end, int) or not isinstance(current_start, int):
        return "", ""
    overlap_len = max(0, previous_end - current_start)
    if overlap_len <= 0:
        return "", ""
    overlap = current["content"][:overlap_len]
    return overlap, overlap


def calculate_report_chunks(db: Session, report_id: int) -> Optional[dict]:
    """Return the same canonical chunks used by vector indexing."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return None

    text_blocks = sorted(report.text_blocks, key=lambda tb: tb.order_index)
    block_dicts = [
        {
            "report_id": report.id,
            "block_id": tb.id,
            "section_type": tb.section_type,
            "section_title": getattr(tb, "section_title", None),
            "source_kind": getattr(tb, "source_kind", None),
            "source_location": getattr(tb, "source_location", None),
            "is_fallback": bool(getattr(tb, "is_fallback", False)),
            "content": tb.content or "",
        }
        for tb in text_blocks
    ]
    chunks = build_chunks(block_dicts, report.id)
    result_chunks = []
    for index, chunk in enumerate(chunks):
        overlap_prev = ""
        overlap_next = ""
        if index > 0:
            overlap_prev, _ = _overlap_for_pair(chunks[index - 1], chunk)
        if index + 1 < len(chunks):
            _, overlap_next = _overlap_for_pair(chunk, chunks[index + 1])
        result_chunks.append(
            {
                "index": index + 1,
                "chunk_id": chunk["chunk_id"],
                "section_type": chunk["section_type"],
                "section_title": chunk.get("section_title"),
                "block_id": chunk.get("block_id"),
                "length": len(chunk["content"]),
                "token_length": chunk["token_length"],
                "start_char": chunk["start_char"],
                "end_char": chunk["end_char"],
                "content": chunk["content"],
                "overlap_prev": overlap_prev,
                "overlap_next": overlap_next,
            }
        )

    return {
        "summary": {
            "total_chunks": len(result_chunks),
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "chunk_unit": "tokens",
            "chunk_version": CHUNK_VERSION,
            "total_text_length": sum(len(tb.content or "") for tb in text_blocks),
            "block_count": len(text_blocks),
        },
        "chunks": result_chunks,
    }
