"""PDF 拆分相关 API

两个核心接口（PHP 端调用）：

  POST /api/splitter/analyze
    - 分析一份 PDF，返回每页类型判定 + 合并后的段
    - 不动文件，纯只读

  POST /api/splitter/execute
    - 按指定的段方案物理拆分 PDF
    - 输出多个子 PDF 到指定目录，返回子文件路径列表
"""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.pdf_splitter import classify_pdf, split_pdf
from app.services.pdf_splitter.splitter import SegmentSpec

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/splitter", tags=["PDF Splitter"])


# ============================================================
# Request / Response 模型
# ============================================================

class AnalyzeRequest(BaseModel):
    """分析请求"""
    file_path: str = Field(..., description="PDF 绝对路径")


class ExecuteSegment(BaseModel):
    """执行拆分时的单段规格（用户在前端可能调整过 type_code）"""
    type_code: str = Field(..., description="目标类型 code，如 customs_declaration")
    page_start: int = Field(..., ge=1)
    page_end: int = Field(..., ge=1)
    output_filename: str = Field(..., description="子 PDF 文件名（不含路径）")


class ExecuteRequest(BaseModel):
    """执行拆分请求"""
    source_pdf: str = Field(..., description="源 PDF 绝对路径")
    output_dir: str = Field(..., description="子文件输出目录")
    segments: list[ExecuteSegment]


# ============================================================
# 接口
# ============================================================

@router.post("/analyze")
async def analyze_pdf(request: AnalyzeRequest):
    """分析 PDF 内容，给出拆分建议

    返回 schema:
    {
      "total_pages": 5,
      "is_scanned": false,
      "suggest_split": true,
      "pages": [
        {"page_no": 1, "type_code": "customs_declaration", "confidence": 95.5, "hits": {...}, "text_preview": "..."},
        ...
      ],
      "segments": [
        {"type_code": "customs_declaration", "page_start": 1, "page_end": 2, "page_count": 2,
         "confidence": 93.0, "page_range": "1-2"},
        {"type_code": "bill_of_lading", "page_start": 3, "page_end": 5, "page_count": 3,
         "confidence": 87.5, "page_range": "3-5"}
      ]
    }
    """
    if not Path(request.file_path).exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {request.file_path}")

    try:
        result = classify_pdf(request.file_path)
        return result.to_dict()
    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析异常: {e}")


@router.post("/execute")
async def execute_split(request: ExecuteRequest):
    """按指定方案拆分 PDF

    返回 schema:
    {
      "success": true,
      "results": [
        {"type_code": "customs_declaration", "page_start": 1, "page_end": 2,
         "output_path": "/abs/path/to/output_1.pdf", "file_size": 123456},
        ...
      ],
      "errors": []
    }
    """
    if not Path(request.source_pdf).exists():
        raise HTTPException(status_code=404, detail=f"源文件不存在: {request.source_pdf}")

    if not request.segments:
        raise HTTPException(status_code=400, detail="未提供任何段")

    specs = [
        SegmentSpec(
            type_code=s.type_code,
            page_start=s.page_start,
            page_end=s.page_end,
            output_filename=s.output_filename,
        )
        for s in request.segments
    ]

    try:
        results, errors = split_pdf(
            source_pdf=request.source_pdf,
            output_dir=request.output_dir,
            segments=specs,
        )

        return {
            "success": len(results) > 0,
            "results": [
                {
                    "type_code": r.type_code,
                    "page_start": r.page_start,
                    "page_end": r.page_end,
                    "output_path": r.output_path,
                    "file_size": r.file_size,
                }
                for r in results
            ],
            "errors": errors,
        }
    except Exception as e:
        logger.error(f"拆分失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"拆分异常: {e}")
