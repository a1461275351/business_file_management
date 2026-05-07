"""
OCR 引擎封装 — 三种模式自动切换

模式优先级 (OCR_ENGINE=auto):
  1. aliyun_api  — 阿里云 qwen-vl-ocr（无需GPU）
  2. local_model — 本地 Logics-Parsing-v2（需GPU）
  3. mock        — 模拟数据（开发调试）
"""

import base64
import json
import logging
import os
import random
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)


class OcrEngine:
    """OCR 引擎 — 统一接口，多后端"""

    def __init__(self):
        self.engine_mode: str = "mock"
        self.model_loaded: bool = False
        self.api_key: str = settings.DASHSCOPE_API_KEY
        self.model_path: str = settings.OCR_MODEL_PATH
        self._init_engine()

    def _init_engine(self):
        """根据配置选择引擎模式"""
        configured = settings.OCR_ENGINE.lower()

        if configured in ("aliyun_api", "auto"):
            if self.api_key:
                self.engine_mode = "aliyun_api"
                logger.info("OCR 引擎: 阿里云 qwen-vl-ocr API")
                return
            elif configured == "aliyun_api":
                logger.warning("DASHSCOPE_API_KEY 未设置，降级为模拟模式")

        if configured in ("local_model", "auto"):
            model_dir = Path(self.model_path) if self.model_path else None
            if model_dir and model_dir.exists():
                self.engine_mode = "local_model"
                self.model_loaded = True
                logger.info(f"OCR 引擎: 本地 Logics-Parsing-v2 ({model_dir})")
                return

        self.engine_mode = "mock"
        logger.info("OCR 引擎: 模拟模式")

    def recognize(self, file_path: str, document_type_code: str, language: str = "zh") -> dict:
        """统一识别接口，返回 {raw_text, fields, overall_confidence, engine_mode, error?}"""
        handler = {
            "aliyun_api": self._recognize_aliyun_api,
            "local_model": self._recognize_local_model,
            "mock": self._recognize_mock,
        }
        fn = handler.get(self.engine_mode, self._recognize_mock)
        result = fn(file_path, document_type_code, language)
        result["engine_mode"] = self.engine_mode
        return result

    # =========================================================
    # 方案A: 阿里云 qwen-vl-ocr（扫描件/图片用）
    # =========================================================
    def _recognize_aliyun_api(self, file_path: str, document_type_code: str, language: str) -> dict:
        try:
            import dashscope

            file_ext = Path(file_path).suffix.lower()

            # PDF 先转图片
            if file_ext == ".pdf":
                images = self._pdf_to_images(file_path)
                if not images:
                    return self._error_result("PDF 转图片失败")
            elif file_ext in (".jpg", ".jpeg", ".png", ".tiff", ".tif"):
                images = [file_path]
            else:
                return self._error_result(f"不支持的文件格式: {file_ext}")

            all_text = []
            for img_path in images:
                img_bytes = Path(img_path).read_bytes()
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                mime = "image/png" if img_path.endswith(".png") else "image/jpeg"
                data_url = f"data:{mime};base64,{b64}"

                prompt = self._build_extraction_prompt(document_type_code)

                messages = [{
                    "role": "user",
                    "content": [
                        {"image": data_url, "min_pixels": 3072, "max_pixels": 1048576},
                        {"text": prompt},
                    ],
                }]

                response = dashscope.MultiModalConversation.call(
                    model="qwen-vl-ocr",
                    api_key=self.api_key,
                    messages=messages,
                )

                if response.status_code == 200:
                    text = response.output.choices[0].message.content[0].get("text", "")
                    all_text.append(text)
                else:
                    error_msg = getattr(response, 'message', str(response.status_code))
                    logger.error(f"阿里云 OCR API 错误: {error_msg}")
                    return self._error_result(f"API错误: {error_msg}")

            raw_text = "\n---\n".join(all_text)
            fields = self._parse_api_response(raw_text, document_type_code)
            overall = sum(f["confidence"] for f in fields) / len(fields) if fields else 0

            return {"raw_text": raw_text, "fields": fields, "overall_confidence": round(overall, 1)}

        except ImportError:
            return self._error_result("dashscope 未安装")
        except Exception as e:
            logger.error(f"阿里云 API 异常: {e}", exc_info=True)
            return self._error_result(str(e))

    def _build_extraction_prompt(self, doc_type: str) -> str:
        prompts = {
            "customs_declaration": "这是一份中国海关报关单。请提取: declaration_no(报关单号), declare_date(申报日期YYYY-MM-DD), hs_code(HS编码), goods_name(货物名称), trade_amount(成交金额纯数字), currency(币种), trade_mode(贸易方式), transport_mode(运输方式), destination_country(目的国), company_name(经营单位)。以JSON数组返回: [{\"field_key\":\"xxx\",\"field_value\":\"xxx\",\"confidence\":95}]",
            "commercial_invoice": "这是一份商业发票。请提取: invoice_no(发票号), invoice_date(开票日期), seller(卖方), buyer(买方), total_amount(总金额纯数字), currency(币种), payment_terms(付款条件), trade_terms(贸易条款)。以JSON数组返回: [{\"field_key\":\"xxx\",\"field_value\":\"xxx\",\"confidence\":95}]",
            "packing_list": "这是一份装箱单。请提取: packing_no(箱单号), total_packages(总件数), gross_weight(毛重KG), net_weight(净重KG), volume_cbm(体积CBM), goods_description(货物描述)。以JSON数组返回。",
            "bill_of_lading": "这是一份提单。请提取: bl_no(提单号), carrier(船公司), port_of_loading(装货港), port_of_discharge(卸货港), container_info(箱型箱量), issue_date(签发日期), shipper(发货人), consignee(收货人)。以JSON数组返回。",
            "bank_receipt": "这是一份银行水单。请提取: transaction_no(流水号), transaction_date(交易日期), amount(金额纯数字), currency(币种), exchange_rate(汇率), counterparty(对手方), purpose(用途)。以JSON数组返回。",
        }
        return prompts.get(doc_type, "请识别文档内容并提取关键字段，以JSON数组返回: [{\"field_key\":\"xxx\",\"field_value\":\"xxx\",\"confidence\":90}]")

    def _parse_api_response(self, raw_text: str, doc_type: str) -> list[dict]:
        """解析 API 返回文本，支持 JSON 数组和对象两种格式"""
        try:
            text = raw_text.strip()
            # 去掉 markdown 代码块
            if "```" in text:
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines).strip()

            # 找 JSON
            for start_char, end_char in [("[", "]"), ("{", "}")]:
                s = text.find(start_char)
                e = text.rfind(end_char)
                if s != -1 and e > s:
                    try:
                        parsed = json.loads(text[s:e + 1])
                        return self._normalize_fields(parsed)
                    except json.JSONDecodeError:
                        continue

            logger.warning("API 返回中未找到有效 JSON")
            return [{"field_key": "raw_text", "field_value": text[:500], "confidence": 60.0, "bbox": None}]

        except Exception as e:
            logger.warning(f"JSON 解析失败: {e}")
            return []

    def _normalize_fields(self, parsed) -> list[dict]:
        """统一字段格式，支持数组和对象"""
        if isinstance(parsed, list):
            return [
                {
                    "field_key": f.get("field_key", ""),
                    "field_value": str(f.get("field_value", "")),
                    "confidence": float(f.get("confidence", 85)) if f.get("field_value") else 0,
                    "bbox": None,
                }
                for f in parsed if f.get("field_key")
            ]

        if isinstance(parsed, dict):
            return [
                {
                    "field_key": key,
                    "field_value": str(value) if value else "",
                    "confidence": 88.0 if value and str(value).strip() else 0,
                    "bbox": None,
                }
                for key, value in parsed.items()
            ]

        return []

    def _pdf_to_images(self, pdf_path: str) -> list[str]:
        """PDF 转图片（pymupdf）"""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            paths = []
            for i in range(min(len(doc), 5)):
                page = doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    pix.save(tmp.name)
                    paths.append(tmp.name)
                    logger.info(f"PDF 第 {i + 1} 页转换: {pix.width}x{pix.height}")
            doc.close()
            return paths
        except ImportError:
            logger.error("pymupdf 未安装")
            return []
        except Exception as e:
            logger.error(f"PDF 转图片失败: {e}")
            return []

    # =========================================================
    # 方案B: 本地 Logics-Parsing-v2
    # =========================================================
    def _recognize_local_model(self, file_path: str, document_type_code: str, language: str) -> dict:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "output"
                output_path.mkdir()
                cmd = [
                    "python3", str(Path(self.model_path) / "inference_v2.py"),
                    "--image_path", file_path,
                    "--output_path", str(output_path),
                    "--model_path", self.model_path,
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=self.model_path)
                if result.returncode != 0:
                    return self._error_result(f"模型推理失败: {result.stderr[:300]}")

                html_content = ""
                for f in output_path.glob("*"):
                    if f.suffix == ".html":
                        html_content = f.read_text(encoding="utf-8")

                return {"raw_text": html_content, "html_content": html_content, "fields": [], "overall_confidence": 95.0}
        except subprocess.TimeoutExpired:
            return self._error_result("模型推理超时")
        except Exception as e:
            return self._error_result(str(e))

    # =========================================================
    # 方案D: 模拟模式
    # =========================================================
    def _recognize_mock(self, file_path: str, document_type_code: str, language: str) -> dict:
        logger.info(f"[模拟模式] 识别: {Path(file_path).name}, 类型: {document_type_code}")
        mock = _MOCK_TEMPLATES.get(document_type_code, _MOCK_DEFAULT)
        fields = [{**f, "confidence": round(f["confidence"] + random.uniform(-2, 2), 1)} for f in mock["fields"]]
        return {"raw_text": f"[模拟] {Path(file_path).name}", "fields": fields, "overall_confidence": mock["confidence"]}

    @staticmethod
    def _error_result(error: str) -> dict:
        return {"raw_text": "", "fields": [], "overall_confidence": 0, "error": error}


# 模拟数据
_MOCK_TEMPLATES = {
    "customs_declaration": {
        "confidence": 96.5,
        "fields": [
            {"field_key": "declaration_no", "field_value": "D260408-MOCK", "confidence": 98.5, "bbox": None},
            {"field_key": "declare_date", "field_value": "2026-04-08", "confidence": 97.2, "bbox": None},
            {"field_key": "hs_code", "field_value": "8542310001", "confidence": 96.8, "bbox": None},
            {"field_key": "goods_name", "field_value": "集成电路芯片", "confidence": 94.5, "bbox": None},
            {"field_key": "trade_amount", "field_value": "48200.00", "confidence": 97.0, "bbox": None},
            {"field_key": "currency", "field_value": "USD", "confidence": 99.0, "bbox": None},
            {"field_key": "trade_mode", "field_value": "一般贸易", "confidence": 72.3, "bbox": None},
            {"field_key": "transport_mode", "field_value": "海运", "confidence": 88.5, "bbox": None},
            {"field_key": "destination_country", "field_value": "US", "confidence": 95.0, "bbox": None},
            {"field_key": "company_name", "field_value": "杨凌国合跨境贸易有限公司", "confidence": 93.2, "bbox": None},
        ],
    },
    "commercial_invoice": {
        "confidence": 95.8,
        "fields": [
            {"field_key": "invoice_no", "field_value": "INV-2026-0088", "confidence": 98.0, "bbox": None},
            {"field_key": "invoice_date", "field_value": "2026-04-08", "confidence": 97.5, "bbox": None},
            {"field_key": "seller", "field_value": "杨凌国合跨境贸易有限公司", "confidence": 94.0, "bbox": None},
            {"field_key": "buyer", "field_value": "ABC Trading Co.", "confidence": 93.5, "bbox": None},
            {"field_key": "total_amount", "field_value": "48200.00", "confidence": 97.8, "bbox": None},
            {"field_key": "currency", "field_value": "USD", "confidence": 99.0, "bbox": None},
        ],
    },
}

_MOCK_DEFAULT = {
    "confidence": 88.0,
    "fields": [{"field_key": "doc_number", "field_value": "DOC-MOCK-001", "confidence": 90.0, "bbox": None}],
}

# 全局单例
ocr_engine = OcrEngine()
