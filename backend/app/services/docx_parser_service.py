import re
import unicodedata
from pathlib import Path
from typing import Iterator, List, Optional

import docx
from docx.document import Document
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from app.core.config import TEMPLATE_NOISE_KEYWORDS


PARSER_VERSION = "2"
MIN_BLOCK_LENGTH = 5
FALLBACK_MIN_LENGTH = 20
MAX_HEADING_LENGTH = 80

# Only aliases that are useful as headings are listed here. Generic words such
# as "总结" are accepted only when the complete (short) line is the heading.
SECTION_ALIASES = {
    "DESIGN_IDEA": (
        "设计思路",
        "系统设计思路",
        "架构设计",
        "系统架构设计",
        "方案设计",
        "总体方案",
        "总体方案设计",
        "模块设计",
    ),
    "REFLECTION": (
        "心得体会",
        "个人体会",
        "实验总结",
        "个人总结与反思",
        "感悟与收获",
        "思考题",
        "思考题回答",
        "总结",
        "感悟",
        "体会",
        "收获",
    ),
}

_NON_TARGET_HEADINGS = {
    "总结与未来展望",
    "系统工作总结",
    "本章小结",
}

_NUMBER_PREFIX_RE = re.compile(
    r"^(?:"
    r"第\s*[0-9０-９一二三四五六七八九十百千万]+\s*[章节部分篇]"
    r"|[0-9０-９]+(?:\s*[.．、]\s*[0-9０-９]+)*\s*[.．、)]?"
    r")\s*"
)
_LIST_PREFIX_RE = re.compile(
    r"^(?:(?:[一二三四五六七八九十百千万]+|[0-9０-９]+)[、.．)）]|[（(][0-9０-９]+[）)])\s*"
)
_HEADING_CONTENT_RE = re.compile(r"^(?P<title>[^:：]{1,80})\s*[:：]\s*(?P<content>.+)$")
_NUMBERED_HEADING_RE = re.compile(
    r"^(?:第\s*[0-9０-９一二三四五六七八九十百千万]+\s*[章节部分篇]|"
    r"[0-9０-９]+(?:\s*[.．、]\s*[0-9０-９]+)+)"
)

STOPWORDS = ("附录", "参考文献", "参考资料", "致谢", "源代码", "源程序")
FRONT_MATTER_PREFIXES = (
    "摘要",
    "关键词",
    "abstract",
    "key words",
    "key words:",
    "图",
    "表",
)


def _normalize_text(text: str) -> str:
    """Normalize layout whitespace without changing punctuation or word order."""
    text = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text or "")).strip()


def _strip_heading_prefix(text: str) -> str:
    value = _normalize_text(text)
    value = _NUMBER_PREFIX_RE.sub("", value, count=1)
    value = _LIST_PREFIX_RE.sub("", value, count=1)
    return value.strip()


def _heading_title(text: str) -> str:
    value = _strip_heading_prefix(text)
    match = _HEADING_CONTENT_RE.match(value)
    return (match.group("title") if match else value).strip()


def _inline_heading_content(text: str) -> str:
    value = _strip_heading_prefix(text)
    match = _HEADING_CONTENT_RE.match(value)
    return _normalize_text(match.group("content")) if match else ""


def _detect_section_type(text: str) -> Optional[str]:
    """Map a short heading to a target section without substring matching."""
    compact = _compact_text(_heading_title(text))
    if not compact or compact in _NON_TARGET_HEADINGS:
        return None

    for section_type, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            if compact == alias:
                return section_type
            # Permit concise suffixes such as "设计思路与实现" while rejecting
            # arbitrary prose that happens to contain the alias.
            suffix = compact[len(alias):] if compact.startswith(alias) else ""
            if suffix in {"与实现", "与分析", "与反思", "回答", "答案"}:
                return section_type
    return None


def _heading_level(paragraph: Optional[Paragraph], text: str) -> Optional[int]:
    """Read Word outline/style level, then fall back to a numeric heading."""
    if paragraph is not None:
        try:
            style_name = str(paragraph.style.name or "")
            match = re.search(r"(?:heading|标题)\s*([1-9])", style_name, re.I)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        try:
            outline = paragraph._p.pPr.outlineLvl if paragraph._p.pPr is not None else None
            if outline is not None and outline.val is not None:
                level = int(outline.val) + 1
                # Word uses outline level 9 for body styles. It is not a
                # heading and must not reset the section state.
                if 1 <= level <= 9:
                    return level
        except Exception:
            pass

    value = _normalize_text(text)
    if re.match(r"^第\s*[0-9０-９一二三四五六七八九十百千万]+\s*[章节部分篇]", value):
        return 1
    match = _NUMBERED_HEADING_RE.match(value)
    if match:
        prefix = match.group(0)
        return len(re.findall(r"[.．、]", prefix)) + 1
    return None


def _looks_like_heading(text: str, paragraph: Optional[Paragraph] = None) -> bool:
    value = _normalize_text(text)
    if not value:
        return False

    # A heading may contain a long inline body after a colon; inspect its title
    # separately before applying the short-line limit.
    title = _heading_title(value)
    title_type = _detect_section_type(title)
    level = _heading_level(paragraph, value)
    if title_type is not None:
        return True
    if level is not None:
        return len(title) <= MAX_HEADING_LENGTH or bool(_NUMBERED_HEADING_RE.match(value))
    if len(value) > MAX_HEADING_LENGTH:
        return False
    if any(ch in value for ch in "。！？；;.!?,，"):
        return False
    return False


def _is_section_title(text: str, paragraph: Optional[Paragraph] = None) -> bool:
    """Backward-compatible title predicate using structural signals."""
    return _looks_like_heading(text, paragraph)


def _is_template_noise(text: str) -> bool:
    value = _strip_heading_prefix(text)
    compact = _compact_text(value).lower()
    return any(compact.startswith(_compact_text(keyword).lower()) for keyword in TEMPLATE_NOISE_KEYWORDS)


def _is_stopword(text: str) -> bool:
    value = _compact_text(_strip_heading_prefix(text)).lower()
    return any(value.startswith(_compact_text(keyword).lower()) for keyword in STOPWORDS)


def _iter_block_items(parent) -> Iterator[object]:
    """Yield paragraphs and tables in XML document order."""
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P

    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Unsupported DOCX parent")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def _iter_textbox_text(paragraph: Paragraph) -> Iterator[str]:
    """Extract text boxes that python-docx does not expose as paragraphs."""
    for txbx in paragraph._p.xpath(".//w:txbxContent"):
        texts = txbx.xpath(".//w:t/text()")
        value = "".join(texts).strip()
        if value:
            yield value


def _iter_units(parent, kind: str = "paragraph", location: Optional[dict] = None) -> Iterator[dict]:
    """Flatten body/table/textbox content while retaining a source location."""
    for block in _iter_block_items(parent):
        if isinstance(block, Paragraph):
            yield {
                "text": block.text,
                "kind": kind,
                "paragraph": block,
                "location": location or {},
            }
            for text in _iter_textbox_text(block):
                yield {
                    "text": text,
                    "kind": "textbox",
                    "paragraph": None,
                    "location": location or {},
                }
        else:
            # A merged cell can occur multiple times in python-docx's row view.
            seen_cells = set()
            for row_index, row in enumerate(block.rows):
                for col_index, cell in enumerate(row.cells):
                    cell_key = id(cell._tc)
                    if cell_key in seen_cells:
                        continue
                    seen_cells.add(cell_key)
                    cell_location = {
                        "table_row": row_index,
                        "table_col": col_index,
                    }
                    yield from _iter_units(cell, "table_cell", cell_location)


def _base_block(unit: dict, section_type: str, content: str, current: Optional[dict], fallback: bool) -> dict:
    return {
        "section_type": section_type,
        "content": content,
        "source_kind": unit.get("kind", "paragraph"),
        "source_index": unit.get("source_index"),
        "source_location": unit.get("location") or {},
        "section_title": (current or {}).get("title"),
        "heading_level": (current or {}).get("level"),
        "fallback": fallback,
        "parser_version": PARSER_VERSION,
    }


def _is_front_matter(text: str) -> bool:
    compact = _compact_text(text).lower()
    return any(compact.startswith(prefix.lower()) for prefix in FRONT_MATTER_PREFIXES)


def parse_docx_report(file_path: str) -> List[dict]:
    """Parse target sections from a DOCX while retaining structural metadata."""
    path = Path(file_path)
    if not path.exists() or path.suffix.lower() != ".docx":
        raise ValueError(f"文件不存在或格式错误: {file_path}")

    doc: Document = docx.Document(str(path))
    blocks: List[dict] = []
    fallback_units: List[dict] = []
    current: Optional[dict] = None
    source_index = 0

    for unit in _iter_units(doc):
        text = (unit.get("text") or "").strip()
        if not text:
            continue
        unit["source_index"] = source_index
        source_index += 1

        if _is_stopword(text):
            break

        heading = _looks_like_heading(text, unit.get("paragraph"))
        title = _heading_title(text)
        section_type = _detect_section_type(text) if heading else None
        level = _heading_level(unit.get("paragraph"), text) if heading else None

        if heading:
            if section_type:
                current = {
                    "type": section_type,
                    "level": level,
                    "title": _normalize_text(title),
                }
                inline = _inline_heading_content(text)
                if len(inline) >= MIN_BLOCK_LENGTH:
                    blocks.append(_base_block(unit, section_type, inline, current, False))
            elif current is not None:
                # A same-level/higher-level non-target heading closes the target
                # section. Unknown-level headings close it conservatively.
                if current.get("level") is None or level is None or level <= current.get("level"):
                    current = None
            continue

        if _is_template_noise(text):
            continue

        normalized = _normalize_text(text)
        if len(normalized) < MIN_BLOCK_LENGTH:
            continue

        if current is not None:
            blocks.append(_base_block(unit, current["type"], normalized, current, False))
        elif len(normalized) >= FALLBACK_MIN_LENGTH and not _is_front_matter(normalized):
            fallback_units.append(unit | {"normalized": normalized})

    if blocks:
        return blocks

    # Conservative fallback: preserve individual paragraphs and mark them so
    # callers can warn or apply a lower confidence policy.
    return [
        _base_block(unit, "GENERAL", unit["normalized"], None, True)
        for unit in fallback_units
    ]


def _merge_adjacent_blocks(blocks: List[dict]) -> List[dict]:
    """Compatibility helper; new parsing keeps source paragraphs separate."""
    if not blocks:
        return []

    merged = [blocks[0].copy()]
    for block in blocks[1:]:
        if block.get("section_type") == merged[-1].get("section_type"):
            merged[-1]["content"] += " " + block.get("content", "")
        else:
            merged.append(block.copy())
    return merged
