"""PDF 自动拆分模块

工作原理:
  1. pdfplumber 逐页提取文字
  2. 关键词匹配判断每页类型
  3. 连续同类型页合并
  4. pymupdf 物理拆分成独立子 PDF
"""

from app.services.pdf_splitter.classifier import classify_pdf, AnalyzeResult
from app.services.pdf_splitter.splitter import split_pdf

__all__ = ["classify_pdf", "AnalyzeResult", "split_pdf"]
