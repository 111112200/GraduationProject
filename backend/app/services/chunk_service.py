from typing import List, Optional
from sqlalchemy.orm import Session

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP
from app.models import Report


def _find_overlap(text_a: str, text_b: str, max_len: int) -> str:
    """
    返回 text_a 的尾部与 text_b 的头部最长公共子串（长度上限为 max_len）。
    由于 RecursiveCharacterTextSplitter 的 overlap 是通过字符位移实现的，
    text_b 的开头必然是 text_a 结尾的某个子串，直接截取匹配即可。
    """
    if not text_a or not text_b or max_len <= 0:
        return ""
    # 取 text_b 开头最多 max_len 个字符，在 text_a 尾部查找
    candidate = text_b[:max_len]
    # 从最长到最短逐步缩短，找到第一个在 text_a 末尾出现的子串
    for length in range(len(candidate), 0, -1):
        sub = candidate[:length]
        if text_a.endswith(sub):
            return sub
    return ""


def calculate_report_chunks(db: Session, report_id: int) -> Optional[dict]:
    """
    对指定报告重新执行文本切分，并为每个 chunk 标记与前后块的重叠区域。
    返回结构：
    {
        "summary": { total_chunks, chunk_size, chunk_overlap, total_text_length, block_count },
        "chunks": [
            {
                "index": 1,
                "section_type": "REFLECTION",
                "length": 480,
                "content": "...",
                "overlap_prev": "..."  # 与上一块末尾重合的内容（即本块头部）
                "overlap_next": "..."  # 与下一块头部重合的内容（即本块尾部）
            },
            ...
        ]
    }
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return None

    # 按 order_index 排序，与入库时保持一致
    text_blocks = sorted(report.text_blocks, key=lambda tb: tb.order_index)
    if not text_blocks:
        return {
            "summary": {
                "total_chunks": 0,
                "chunk_size": CHUNK_SIZE,
                "chunk_overlap": CHUNK_OVERLAP,
                "total_text_length": 0,
                "block_count": 0,
            },
            "chunks": [],
        }

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "。", "！", "？", "\n"],
        length_function=len,
    )

    raw_chunks = []
    total_text_length = 0
    for tb in text_blocks:
        content = tb.content or ""
        total_text_length += len(content)
        for piece in splitter.split_text(content):
            # 去除分块后可能遗留在开头的标点符号和空白字符
            piece = piece.lstrip("。！？\n\r\t ")
            if len(piece.strip()) >= 10:
                raw_chunks.append({
                    "section_type": tb.section_type,
                    "content": piece,
                })

    result_chunks = []
    for i, chunk in enumerate(raw_chunks):
        text = chunk["content"]

        # 计算与前块的重叠（本块头部 = 前块尾部的某个后缀）
        if i > 0:
            overlap_prev = _find_overlap(raw_chunks[i - 1]["content"], text, CHUNK_OVERLAP)
        else:
            overlap_prev = ""

        # 计算与后块的重叠（本块尾部 = 后块头部的某个前缀）
        if i < len(raw_chunks) - 1:
            overlap_next = _find_overlap(text, raw_chunks[i + 1]["content"], CHUNK_OVERLAP)
        else:
            overlap_next = ""

        result_chunks.append({
            "index": i + 1,
            "section_type": chunk["section_type"],
            "length": len(text),
            "content": text,
            "overlap_prev": overlap_prev,
            "overlap_next": overlap_next,
        })

    return {
        "summary": {
            "total_chunks": len(result_chunks),
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "total_text_length": total_text_length,
            "block_count": len(text_blocks),
        },
        "chunks": result_chunks,
    }
