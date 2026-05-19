import re
from pathlib import Path
from typing import List, Optional, Tuple

import docx
from docx.document import Document
from docx.text.paragraph import Paragraph

from app.core.config import TARGET_SECTION_KEYWORDS, TEMPLATE_NOISE_KEYWORDS

MIN_BLOCK_LENGTH = 5  # 最小文本块长度（字符），兼容短句


def _normalize_text(text: str) -> str:
    """去除多余空格、换行等"""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _is_section_title(text: str) -> bool:
    """判断是否为章节标题（设计思路、心得体会等）"""
    for kw in TARGET_SECTION_KEYWORDS:
        if kw in text or text.strip().startswith(kw):
            return True
    return False


def _detect_section_type(text: str) -> Optional[str]:
    """将标题映射为内部类型"""
    if "设计思路" in text:
        return "DESIGN_IDEA"
    reflection_kws = ["心得体会", "个人体会", "实验总结", "总结", "感悟", "体会", "收获"]
    if any(kw in text for kw in reflection_kws):
        return "REFLECTION"
    return None


def _is_template_noise(text: str) -> bool:
    """判断是否为模板噪音（实验目的、实验原理等）"""
    text_lower = text.strip()
    for kw in TEMPLATE_NOISE_KEYWORDS:
        if text_lower.startswith(kw):
            return True
    return False


def parse_docx_report(file_path: str) -> List[dict]:
    """
    解析 .docx 实验报告，提取设计思路、心得体会等目标段落。
    支持段落以及表格内的文本抽取。
    如果按章节标题提取不到任何内容，则回退为提取全文有效段落。
    """
    path = Path(file_path)
    if not path.exists() or path.suffix.lower() != ".docx":
        raise ValueError(f"文件不存在或格式错误: {file_path}")

    doc: Document = docx.Document(str(path))
    blocks: List[dict] = []
    all_paragraphs: List[str] = []  # 用于 fallback 的全文段落
    current_section_type: Optional[str] = None

    def process_text(text: str):
        nonlocal current_section_type
        if not text:
            return

        # 收集所有有效段落（用于 fallback）
        normalized = _normalize_text(text)
        if len(normalized) >= MIN_BLOCK_LENGTH and not _is_template_noise(text):
            all_paragraphs.append(normalized)

        # 1. 判断是否为标题行
        if _is_section_title(text):
            st = _detect_section_type(text)
            if st:
                current_section_type = st
                # 处理标题和内容在同一段的情况（例如："心得体会：这次实验..."）
                parts = re.split(r'[:：\s]+', text, maxsplit=1)
                if len(parts) > 1 and len(parts[1].strip()) > MIN_BLOCK_LENGTH:
                    content = _normalize_text(parts[1])
                    blocks.append({
                        "section_type": current_section_type,
                        "content": content,
                    })
            return

        # 2. 过滤模板噪音
        if _is_template_noise(text):
            return

        # 3. 仅记录目标段落
        if current_section_type in ("DESIGN_IDEA", "REFLECTION"):
            content = _normalize_text(text)
            if len(content) >= MIN_BLOCK_LENGTH:
                blocks.append({
                    "section_type": current_section_type,
                    "content": content,
                })

    def iter_block_items(parent):
        """
        Yield each paragraph and table child within *parent*, in document order.
        """
        from docx.document import Document
        from docx.oxml.text.paragraph import CT_P
        from docx.oxml.table import CT_Tbl
        from docx.table import _Cell, Table
        from docx.text.paragraph import Paragraph

        if isinstance(parent, Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("Something's wrong")

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    stopwords = ["附录", "参考文献", "致谢", "致  谢", "参考资料", "源代码", "源程序"]

    def _is_stopword(text: str) -> bool:
        text_lower = text.strip().replace(" ", "")
        for kw in stopwords:
            if text_lower.startswith(kw):
                return True
        return False

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if _is_stopword(text):
                break
            process_text(text)
            
            # 额外处理段落中嵌入的文本框(TextBox)
            # 文本框的内容在 w:drawing/wp:inline/a:graphic/.../w:txbxContent 
            # 或 v:textbox/w:txbxContent 中
            p_xml = block._p
            # python-docx 的 BaseOxmlElement.xpath() 已内置 Word 命名空间
            txbx_nodes = p_xml.xpath('.//w:txbxContent')
            for txbx in txbx_nodes:
                # 提取里面的 w:t
                texts = txbx.xpath('.//w:t/text()')
                if texts:
                    txbx_text = "".join(texts).strip()
                    if txbx_text:
                        if _is_stopword(txbx_text):
                            break
                        process_text(txbx_text)
            
        else:  # Table
            for row in block.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    lines = cell_text.split('\n')
                    for line in lines:
                        if _is_stopword(line.strip()):
                            break
                        process_text(line.strip())

    # 合并同类型相邻段落
    merged = _merge_adjacent_blocks(blocks)

    # Fallback: 如果按章节提取为空，则使用全文有效段落
    if not merged and all_paragraphs:
        # 过滤掉过短和章节标题本身的段落
        fallback_texts = [
            p for p in all_paragraphs
            if len(p) >= MIN_BLOCK_LENGTH and not _is_section_title(p)
        ]
        if fallback_texts:
            merged = [{"section_type": "GENERAL", "content": t} for t in fallback_texts]
            merged = _merge_adjacent_blocks(merged)

    return merged


def _merge_adjacent_blocks(blocks: List[dict]) -> List[dict]:
    """合并同一 section 下连续段落"""
    if not blocks:
        return []

    merged = [blocks[0].copy()]
    for i in range(1, len(blocks)):
        if blocks[i]["section_type"] == merged[-1]["section_type"]:
            merged[-1]["content"] += " " + blocks[i]["content"]
        else:
            merged.append(blocks[i].copy())
    return merged
