"""PDF 分类器 — 逐页判断文件类型，连续同类型合并为段

输入: PDF 文件路径
输出: AnalyzeResult，包含每页的类型判定 + 合并后的段（每段对应一个待生成的子文档）

依赖：pdfplumber（提取页面文字）
扫描件兜底：pdfplumber 提取失败时，page_text 为空，类型判定为 "unknown"
"""

import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

from app.services.pdf_splitter.keywords import (
    TYPE_KEYWORDS,
    TYPE_PRIORITY,
    MIN_HITS,
    count_hits,
)

logger = logging.getLogger(__name__)


@dataclass
class PageClassification:
    """单页的分类结果"""
    page_no: int                # 第几页（从 1 开始）
    type_code: str              # 判定的类型 code；不确定时为 "unknown"
    confidence: float           # 置信度 0-100
    hits: dict                  # 各类型命中关键词数 {"customs_declaration": 5, ...}
    text_preview: str           # 该页文字前 200 字（调试用）


@dataclass
class Segment:
    """一段连续同类型的页范围 → 对应一个待生成的子文档"""
    type_code: str
    page_start: int             # 起始页（含，从 1 开始）
    page_end: int               # 结束页（含）
    confidence: float           # 段平均置信度
    page_count: int

    @property
    def page_range_str(self) -> str:
        """页范围字符串：'1-2' 或 '5'"""
        if self.page_start == self.page_end:
            return str(self.page_start)
        return f"{self.page_start}-{self.page_end}"


@dataclass
class AnalyzeResult:
    """完整分析结果"""
    total_pages: int
    is_scanned: bool                            # 是否为扫描件（无法提取文字）
    pages: list[PageClassification] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    suggest_split: bool = False                 # 是否建议拆分（segments 数 > 1）

    def to_dict(self) -> dict:
        return {
            "total_pages": self.total_pages,
            "is_scanned": self.is_scanned,
            "suggest_split": self.suggest_split,
            "pages": [asdict(p) for p in self.pages],
            "segments": [
                {
                    "type_code": s.type_code,
                    "page_start": s.page_start,
                    "page_end": s.page_end,
                    "page_count": s.page_count,
                    "confidence": s.confidence,
                    "page_range": s.page_range_str,
                }
                for s in self.segments
            ],
        }


def _classify_page(page_text: str, page_no: int) -> PageClassification:
    """对单页文本做类型判定"""
    if not page_text or len(page_text.strip()) < 20:
        # 文字过少（扫描件或空页）
        return PageClassification(
            page_no=page_no,
            type_code="unknown",
            confidence=0.0,
            hits={},
            text_preview="",
        )

    # 对每种类型统计命中数
    hits_per_type = {}
    for type_code, keywords in TYPE_KEYWORDS.items():
        n, _ = count_hits(page_text, keywords)
        hits_per_type[type_code] = n

    # 找命中最多的类型，达到 MIN_HITS 才认定
    max_hits = max(hits_per_type.values()) if hits_per_type else 0

    if max_hits < MIN_HITS:
        return PageClassification(
            page_no=page_no,
            type_code="unknown",
            confidence=0.0,
            hits=hits_per_type,
            text_preview=page_text[:200],
        )

    # 候选类型（命中数等于最大值的）
    candidates = [t for t, n in hits_per_type.items() if n == max_hits]
    # 按优先级排序，取第一个
    candidates.sort(key=lambda t: TYPE_PRIORITY.get(t, 99))
    best_type = candidates[0]

    # 置信度公式：命中数 / 该类关键词总数 * 100，上限 99
    total_kw = len(TYPE_KEYWORDS[best_type])
    confidence = min(99.0, round(max_hits / total_kw * 100 * 2, 1))  # 乘 2 让命中 50% 关键词时就接近 100

    return PageClassification(
        page_no=page_no,
        type_code=best_type,
        confidence=confidence,
        hits=hits_per_type,
        text_preview=page_text[:200],
    )


def _merge_segments(pages: list[PageClassification]) -> list[Segment]:
    """把连续同类型的页合并为段

    - "unknown" 页若夹在两个相同类型之间，归并到该类型（处理表格延续页等情况）
    - 否则 unknown 段独立保留（用户可手动指定类型）
    """
    if not pages:
        return []

    # 第一遍：unknown 夹心合并
    # 例如 [A, A, unknown, A, B] → [A, A, A, A, B]
    cleaned = [p.type_code for p in pages]
    for i in range(1, len(cleaned) - 1):
        if cleaned[i] == "unknown":
            left_type = cleaned[i - 1]
            right_type = cleaned[i + 1]
            if left_type == right_type and left_type != "unknown":
                cleaned[i] = left_type

    # 第二遍：分组合并
    segments = []
    seg_start_idx = 0
    for i in range(1, len(cleaned) + 1):
        if i == len(cleaned) or cleaned[i] != cleaned[seg_start_idx]:
            # 一段结束
            seg_pages = pages[seg_start_idx:i]
            type_code = cleaned[seg_start_idx]
            avg_conf = sum(p.confidence for p in seg_pages) / len(seg_pages)
            segments.append(Segment(
                type_code=type_code,
                page_start=seg_pages[0].page_no,
                page_end=seg_pages[-1].page_no,
                confidence=round(avg_conf, 1),
                page_count=len(seg_pages),
            ))
            seg_start_idx = i

    return segments


def classify_pdf(file_path: str) -> AnalyzeResult:
    """主入口：分析一个 PDF，返回每页类型 + 合并的段

    Args:
        file_path: PDF 文件绝对路径

    Returns:
        AnalyzeResult: 含每页判定和合并后的段
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber 未安装，无法分类")
        return AnalyzeResult(total_pages=0, is_scanned=True)

    path = Path(file_path)
    if not path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return AnalyzeResult(total_pages=0, is_scanned=False)

    # 仅 PDF 适用
    if path.suffix.lower() != ".pdf":
        logger.info(f"非 PDF 文件，不进行拆分分类: {file_path}")
        return AnalyzeResult(total_pages=1, is_scanned=False)

    pages_classified: list[PageClassification] = []
    is_scanned = True  # 假定全是扫描件，直到看到有效文字

    try:
        with pdfplumber.open(str(path)) as pdf:
            total = len(pdf.pages)
            for idx, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    logger.warning(f"第 {idx + 1} 页文字提取异常: {e}")
                    text = ""

                if len(text.strip()) >= 20:
                    is_scanned = False  # 至少有一页有文字

                pages_classified.append(_classify_page(text, idx + 1))

    except Exception as e:
        logger.error(f"PDF 打开失败: {e}", exc_info=True)
        return AnalyzeResult(total_pages=0, is_scanned=False)

    segments = _merge_segments(pages_classified)

    # 拆分建议：段数 > 1，或唯一段不是 unknown 时也可以保留单段（不拆）
    distinct_known = [s for s in segments if s.type_code != "unknown"]
    suggest_split = len(segments) > 1 and len(distinct_known) >= 1

    result = AnalyzeResult(
        total_pages=total,
        is_scanned=is_scanned,
        pages=pages_classified,
        segments=segments,
        suggest_split=suggest_split,
    )

    logger.info(
        f"分类完成: file={path.name}, pages={total}, segments={len(segments)}, "
        f"scanned={is_scanned}, suggest_split={suggest_split}"
    )
    return result
