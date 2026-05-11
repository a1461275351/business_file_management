"""PDF 物理拆分器 — pymupdf 把一份 PDF 按页范围切成多个子 PDF

输入: 源 PDF 路径 + 段列表（每段含 page_start / page_end / type_code 等）
输出: 每段对应的子 PDF 文件物理路径

依赖：pymupdf (fitz)
"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SegmentSpec:
    """拆分规格 — 由调用方（PHP/前端确认后）传入"""
    type_code: str          # 目标类型 code
    page_start: int         # 起始页（含，从 1 开始）
    page_end: int           # 结束页（含）
    output_filename: str    # 子 PDF 输出文件名（不含路径）


@dataclass
class SplitResult:
    """单段拆分输出"""
    type_code: str
    page_start: int
    page_end: int
    output_path: str        # 完整路径
    file_size: int          # 字节


def split_pdf(
    source_pdf: str,
    output_dir: str,
    segments: list[SegmentSpec],
) -> tuple[list[SplitResult], list[str]]:
    """按段拆分 PDF

    Args:
        source_pdf: 源 PDF 绝对路径
        output_dir: 输出目录（必须已存在或本函数创建）
        segments: 拆分规格列表

    Returns:
        (成功拆分的结果列表, 错误信息列表)
    """
    try:
        import fitz  # pymupdf
    except ImportError:
        return [], ["pymupdf 未安装"]

    src_path = Path(source_pdf)
    if not src_path.exists():
        return [], [f"源文件不存在: {source_pdf}"]

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[SplitResult] = []
    errors: list[str] = []

    try:
        src = fitz.open(str(src_path))
        total_pages = len(src)

        for seg in segments:
            # 校验页范围
            if seg.page_start < 1 or seg.page_end > total_pages or seg.page_start > seg.page_end:
                errors.append(
                    f"段 [{seg.page_start}-{seg.page_end}] 超出范围 (总 {total_pages} 页)"
                )
                continue

            try:
                # 新文档：复制源 PDF 的指定页范围
                # fitz 页码从 0 开始，传入区间 [start, stop] 闭区间
                new_doc = fitz.open()
                new_doc.insert_pdf(
                    src,
                    from_page=seg.page_start - 1,
                    to_page=seg.page_end - 1,
                )

                output_path = out_dir / seg.output_filename
                # garbage=4: 最大压缩；deflate=True: 启用流压缩
                new_doc.save(str(output_path), garbage=4, deflate=True)
                new_doc.close()

                size = output_path.stat().st_size
                results.append(SplitResult(
                    type_code=seg.type_code,
                    page_start=seg.page_start,
                    page_end=seg.page_end,
                    output_path=str(output_path).replace("\\", "/"),
                    file_size=size,
                ))
                logger.info(
                    f"拆分成功: {seg.output_filename} "
                    f"(页 {seg.page_start}-{seg.page_end}, {size} 字节)"
                )

            except Exception as e:
                errors.append(f"段 [{seg.page_start}-{seg.page_end}] 拆分失败: {e}")
                logger.error(f"段拆分异常: {e}", exc_info=True)

        src.close()

    except Exception as e:
        return [], [f"打开源 PDF 失败: {e}"]

    return results, errors
