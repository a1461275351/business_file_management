"""Pydantic 请求/响应模型"""

from pydantic import BaseModel
from typing import Optional


class OcrRequest(BaseModel):
    document_id: int
    file_path: str
    document_type_code: str
    language: str = "zh"


class OcrFieldResult(BaseModel):
    field_key: str
    field_value: str
    confidence: float
    bbox: Optional[dict] = None  # {page, x, y, w, h}


class OcrResponse(BaseModel):
    document_id: int
    success: bool
    fields: list[OcrFieldResult] = []
    raw_text: str = ""
    overall_confidence: float = 0.0
    error: Optional[str] = None


class FieldExtractRequest(BaseModel):
    document_id: int
    raw_text: str
    document_type_code: str
    html_content: Optional[str] = None  # Logics-Parsing 输出的 HTML


class CrossCheckRequest(BaseModel):
    order_id: int


class CrossCheckAlert(BaseModel):
    alert_type: str
    severity: str
    description: str
    document_id: int
    related_document_id: Optional[int] = None
    detail: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    ocr_engine: str
    ocr_model_loaded: bool
    db_connected: bool
