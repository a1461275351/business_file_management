"""
文档处理器 — 智能提取策略

优先级：
  1. pdfplumber/python-docx 直接提取文字（免费、精准、适合电子版PDF/Word）
  2. 阿里云 qwen-vl-ocr API（适合扫描件/图片）
  3. 本地 Logics-Parsing-v2 模型（需GPU）
  4. 模拟数据（开发调试）

缓存：OCR结果存入 MySQL ocr_cache 表（3天有效），添加字段时自动匹配
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.services.ocr.engine import ocr_engine
from app.services.ocr.text_extractor import text_extractor

logger = logging.getLogger(__name__)


class OcrProcessor:
    """文档处理器"""

    def process_task(self, db: Session, task_id: int) -> dict:
        """
        处理一个 OCR 任务

        流程: 取任务 → 定位文件 → 尝试文字提取 → 提取失败则调OCR → 匹配字段 → 写库 → 缓存
        """
        # 1. 获取任务和文件信息
        task = db.execute(
            text("SELECT * FROM ocr_tasks WHERE id = :id"), {"id": task_id}
        ).mappings().first()

        if not task:
            return {"success": False, "error": f"任务 {task_id} 不存在"}
        if task["status"] not in ("pending", "retry"):
            return {"success": False, "error": f"任务状态不允许: {task['status']}"}

        document_id = task["document_id"]

        doc = db.execute(
            text("SELECT d.*, dt.code as type_code FROM documents d "
                 "JOIN document_types dt ON d.document_type_id = dt.id "
                 "WHERE d.id = :id"),
            {"id": document_id}
        ).mappings().first()

        if not doc:
            self._fail_task(db, task_id, "文件不存在")
            return {"success": False, "error": "文件不存在"}

        # 2. 更新任务状态
        db.execute(
            text("UPDATE ocr_tasks SET status = 'processing', started_at = :now, "
                 "worker_id = 'python-api' WHERE id = :id"),
            {"id": task_id, "now": datetime.now()}
        )
        db.commit()

        try:
            # 3. 定位文件
            file_path = Path(settings.FILE_STORAGE_PATH) / doc["storage_path"]
            if not file_path.exists():
                self._fail_task(db, task_id, f"文件不存在: {file_path}")
                return {"success": False, "error": f"文件不存在: {file_path}"}

            # 4. 智能提取策略
            logger.info(f"开始处理: doc_id={document_id}, file={file_path}")

            # 4a. 先尝试直接文字提取（免费、精准）
            extract_result = text_extractor.extract(str(file_path))

            if extract_result["success"]:
                logger.info(f"文字提取成功 ({extract_result['method']}): "
                           f"{len(extract_result['text'])}字, "
                           f"{len(extract_result['tables'])}个表格")

                # 用提取的文字 + AI 解析字段
                result = self._parse_text_to_fields(
                    extract_result["text"],
                    extract_result["tables"],
                    doc["type_code"],
                )
                result["engine_mode"] = f"text_extract:{extract_result['method']}"
            else:
                # 4b. 文字提取失败（扫描件/图片）→ 调 OCR 引擎
                logger.info("文字提取失败，回退到 OCR 引擎")
                result = ocr_engine.recognize(
                    file_path=str(file_path),
                    document_type_code=doc["type_code"],
                    language=doc["language"] or "zh",
                )

            if result.get("error"):
                self._fail_task(db, task_id, result["error"])
                return {"success": False, "error": result["error"]}

            # 5. 获取字段模板
            templates = db.execute(
                text("SELECT * FROM field_templates WHERE document_type_id = :type_id "
                     "AND status = 1 ORDER BY sort_order"),
                {"type_id": doc["document_type_id"]}
            ).mappings().all()
            template_map = {t["field_key"]: t for t in templates}

            # 6. 写入字段值
            fields_saved = 0
            for field in result.get("fields", []):
                field_key = field["field_key"]
                template = template_map.get(field_key)
                if not template:
                    continue

                existing = db.execute(
                    text("SELECT id, is_confirmed, field_value FROM document_fields "
                         "WHERE document_id = :doc_id AND field_key = :fk"),
                    {"doc_id": document_id, "fk": field_key}
                ).first()

                bbox_json = json.dumps(field["bbox"]) if field.get("bbox") else None
                new_value = field["field_value"]
                new_conf = field["confidence"]

                if existing:
                    # existing = (id, is_confirmed, field_value)
                    is_confirmed = bool(existing[1])
                    has_value = bool(existing[2] and str(existing[2]).strip())
                    if is_confirmed and has_value:
                        # 已人工确认且有值，不覆盖
                        logger.debug(f"字段 {field_key} 已确认，跳过")
                        fields_saved += 1
                        continue
                    db.execute(
                        text("UPDATE document_fields SET field_value = :val, "
                             "confidence = :conf, bbox_info = :bbox, "
                             "extract_method = :method, is_confirmed = 0, "
                             "updated_at = :now WHERE id = :id"),
                        {
                            "id": existing[0], "val": new_value,
                            "conf": new_conf, "bbox": bbox_json,
                            "method": "auto_ocr" if "aliyun_api" in result.get("engine_mode", "") or "local_model" in result.get("engine_mode", "") else "auto_nlp",
                            "now": datetime.now(),
                        }
                    )
                else:
                    db.execute(
                        text("INSERT INTO document_fields "
                             "(document_id, field_template_id, field_key, field_value, "
                             "confidence, extract_method, bbox_info, is_confirmed, "
                             "created_at, updated_at) "
                             "VALUES (:doc_id, :tmpl_id, :fk, :val, :conf, "
                             ":method, :bbox, 0, :now, :now)"),
                        {
                            "doc_id": document_id,
                            "tmpl_id": template["id"],
                            "fk": field_key,
                            "val": new_value,
                            "conf": new_conf,
                            "method": "auto_ocr" if "aliyun_api" in result.get("engine_mode", "") or "local_model" in result.get("engine_mode", "") else "auto_nlp",
                            "bbox": bbox_json,
                            "now": datetime.now(),
                        }
                    )
                fields_saved += 1

            # 7. 更新文件状态
            overall_confidence = result.get("overall_confidence", 0)
            has_low_conf = any(
                f["confidence"] < settings.OCR_CONFIDENCE_THRESHOLD
                for f in result.get("fields", [])
                if f.get("field_value")
            )
            new_status = "pending_review" if has_low_conf else "pending_approval"

            total_required = sum(1 for t in templates if t["is_required"])
            filled_required = sum(
                1 for f in result.get("fields", [])
                if f.get("field_value") and template_map.get(f["field_key"], {}).get("is_required")
            )
            field_rate = (filled_required / total_required * 100) if total_required > 0 else 100

            db.execute(
                text("UPDATE documents SET status = :status, ocr_confidence = :conf, "
                     "field_complete_rate = :rate, updated_at = :now WHERE id = :id"),
                {"id": document_id, "status": new_status, "conf": overall_confidence,
                 "rate": round(field_rate, 1), "now": datetime.now()}
            )

            # 8. 缓存结果到数据库（3天有效）
            cache_data = json.dumps({
                "raw_text": result.get("raw_text", ""),
                "fields": result.get("fields", []),
                "overall_confidence": overall_confidence,
                "engine_mode": result.get("engine_mode", ""),
            }, ensure_ascii=False)
            self._save_cache(db, document_id, cache_data, result.get("engine_mode", ""))

            # 9. 完成任务
            db.execute(
                text("UPDATE ocr_tasks SET status = 'completed', completed_at = :now, "
                     "result_summary = :summary WHERE id = :id"),
                {"id": task_id, "now": datetime.now(),
                 "summary": json.dumps({
                     "fields_extracted": fields_saved,
                     "overall_confidence": overall_confidence,
                     "engine_mode": result.get("engine_mode", ""),
                     "new_status": new_status,
                 })}
            )
            db.commit()

            logger.info(f"处理完成: doc_id={document_id}, mode={result.get('engine_mode')}, "
                       f"fields={fields_saved}, confidence={overall_confidence}, status→{new_status}")

            return {
                "success": True,
                "document_id": document_id,
                "fields_extracted": fields_saved,
                "overall_confidence": overall_confidence,
                "engine_mode": result.get("engine_mode", ""),
                "new_status": new_status,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"处理异常: {e}", exc_info=True)
            self._fail_task(db, task_id, str(e))
            return {"success": False, "error": str(e)}

    def _parse_text_to_fields(self, text: str, tables: list, doc_type: str) -> dict:
        """
        用提取的文字解析字段（不调 OCR，直接用 AI 或规则匹配）

        先尝试调阿里云 AI 做文字理解，如果没有 API Key 则用正则匹配
        """
        import os

        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if api_key:
            return self._parse_with_ai(text, tables, doc_type, api_key)
        else:
            return self._parse_with_rules(text, tables, doc_type)

    def _parse_with_ai(self, text: str, tables: list, doc_type: str, api_key: str) -> dict:
        """用阿里云通义千问文本模型解析字段（比 OCR 便宜得多）"""
        try:
            import dashscope

            prompt = self._build_text_prompt(doc_type, text, tables)

            response = dashscope.Generation.call(
                model="qwen-plus",
                api_key=api_key,
                messages=[{"role": "user", "content": prompt}],
            )

            if response.status_code == 200:
                # 兼容 dashscope 不同版本的返回格式
                output = response.output
                result_text = ""
                try:
                    if hasattr(output, 'choices') and output.choices:
                        result_text = output.choices[0].message.content
                    elif hasattr(output, 'text') and output.text:
                        result_text = output.text
                    elif isinstance(output, dict):
                        result_text = output.get('text', '') or output.get('choices', [{}])[0].get('message', {}).get('content', '')
                    else:
                        result_text = str(output)
                except (IndexError, AttributeError, TypeError):
                    result_text = str(output)

                logger.info(f"AI 解析返回: {result_text[:200]}...")
                fields = ocr_engine._parse_api_response(result_text, doc_type)

                # 文字提取的字段置信度更高
                for f in fields:
                    if f["confidence"] > 0:
                        f["confidence"] = min(f["confidence"] + 5, 99)

                overall = sum(f["confidence"] for f in fields) / len(fields) if fields else 0
                return {
                    "raw_text": text,
                    "fields": fields,
                    "overall_confidence": round(overall, 1),
                }
            else:
                logger.warning(f"AI 解析失败: {response.code}")
                return self._parse_with_rules(text, tables, doc_type)

        except Exception as e:
            logger.warning(f"AI 解析异常: {e}")
            return self._parse_with_rules(text, tables, doc_type)

    def _parse_with_rules(self, text: str, tables: list, doc_type: str) -> dict:
        """用正则规则匹配字段（完全免费，不调任何 API）"""
        import re

        fields = []

        rules = {
            "customs_declaration": {
                "declaration_no": [r"预录入编号[：:]\s*(\S+)", r"报关单号[：:]\s*(\S+)"],
                "declare_date": [r"申报日期[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})"],
                "hs_code": [r"商品编号[：:]\s*(\d{8,10})", r"HS[编編]码[：:]\s*(\d{8,10})"],
                "goods_name": [r"商品名称[：:]\s*(.+?)(?:\s{2,}|$)"],
                "trade_amount": [r"成交总价[：:]\s*([\d,.]+)", r"总价[：:]\s*([\d,.]+)"],
                "currency": [r"币制[：:]\s*(\w+)", r"(USD|CNY|EUR|JPY)"],
                "trade_mode": [r"监管方式[：:]\s*(.+?)(?:\s{2,}|$)", r"贸易方式[：:]\s*(.+?)(?:\s{2,}|$)"],
                "transport_mode": [r"运输方式[：:]\s*(.+?)(?:\s{2,}|$)"],
                "destination_country": [r"运抵国[：:]\s*(.+?)(?:\s{2,}|$)", r"目的国[：:]\s*(.+?)(?:\s{2,}|$)"],
                "company_name": [r"经营单位[：:]\s*(.+?)(?:\s{2,}|$)", r"收发货人[：:]\s*(.+?)(?:\s{2,}|$)"],
            },
            "commercial_invoice": {
                "invoice_no": [r"[Ii]nvoice\s*[Nn]o\.?\s*[：:]\s*(\S+)", r"发票号[：:]\s*(\S+)"],
                "invoice_date": [r"[Dd]ate[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})"],
                "total_amount": [r"[Tt]otal[：:]\s*([\d,.]+)", r"合计[：:]\s*([\d,.]+)"],
                "currency": [r"(USD|CNY|EUR|JPY)"],
            },
        }

        type_rules = rules.get(doc_type, {})
        for field_key, patterns in type_rules.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    value = match.group(1).strip()
                    if value:
                        fields.append({
                            "field_key": field_key,
                            "field_value": value,
                            "confidence": 85.0,
                            "bbox": None,
                        })
                        break
            else:
                fields.append({
                    "field_key": field_key,
                    "field_value": "",
                    "confidence": 0,
                    "bbox": None,
                })

        overall = sum(f["confidence"] for f in fields) / len(fields) if fields else 0
        return {
            "raw_text": text,
            "fields": fields,
            "overall_confidence": round(overall, 1),
        }

    def _build_text_prompt(self, doc_type: str, text: str, tables: list) -> str:
        """构建文字理解提示词"""
        table_text = ""
        for t in tables[:3]:
            table_text += f"\n表格: {' | '.join(t.get('headers', []))}\n"
            for row in t.get("rows", [])[:5]:
                table_text += f"  {' | '.join(row)}\n"

        type_fields = {
            "customs_declaration": "declaration_no(报关单号), declare_date(申报日期), hs_code(HS编码), goods_name(货物名称), trade_amount(成交金额), currency(币种), trade_mode(贸易方式), transport_mode(运输方式), destination_country(目的国), company_name(经营单位)",
            "commercial_invoice": "invoice_no(发票号), invoice_date(开票日期), seller(卖方), buyer(买方), total_amount(总金额), currency(币种), payment_terms(付款条件)",
            "packing_list": "packing_no(箱单号), total_packages(总件数), gross_weight(毛重), net_weight(净重), volume_cbm(体积)",
            "bill_of_lading": "bl_no(提单号), carrier(船公司), port_of_loading(装货港), port_of_discharge(卸货港), issue_date(签发日期)",
        }

        fields_desc = type_fields.get(doc_type, "提取所有关键字段")

        return (
            f"以下是从文档中提取的文字内容：\n\n{text[:3000]}\n{table_text}\n\n"
            f"请从上述内容中提取以下字段，以JSON数组格式返回：\n{fields_desc}\n"
            f"返回格式: [{{\"field_key\":\"xxx\",\"field_value\":\"xxx\",\"confidence\":95}}]\n"
            f"如果某个字段在文档中找不到，field_value 设为空字符串，confidence 设为 0。"
        )

    def _fail_task(self, db: Session, task_id: int, error: str):
        """标记任务失败"""
        db.execute(
            text("UPDATE ocr_tasks SET status = 'failed', "
                 "error_message = :err, completed_at = :now WHERE id = :id"),
            {"id": task_id, "err": error[:1000], "now": datetime.now()}
        )
        db.commit()

    def _save_cache(self, db: Session, document_id: int, cache_data: str, engine_mode: str):
        """保存结果到数据库缓存（3天有效）"""
        try:
            db.execute(text("DELETE FROM ocr_cache WHERE document_id = :doc_id"), {"doc_id": document_id})
            db.execute(
                text("INSERT INTO ocr_cache (document_id, raw_result, engine_mode, expires_at) "
                     "VALUES (:doc_id, :raw, :engine, :expires)"),
                {"doc_id": document_id, "raw": cache_data, "engine": engine_mode,
                 "expires": datetime.now() + timedelta(days=3)}
            )
            logger.info(f"缓存已保存: doc_id={document_id}, mode={engine_mode}")
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")

    @staticmethod
    def get_cache(document_id: int) -> dict | None:
        """从数据库读取缓存"""
        try:
            from app.models.database import SessionLocal
            db = SessionLocal()
            row = db.execute(
                text("SELECT raw_result FROM ocr_cache "
                     "WHERE document_id = :doc_id AND expires_at > :now"),
                {"doc_id": document_id, "now": datetime.now()}
            ).first()
            db.close()
            if row:
                return json.loads(row[0])
        except Exception:
            pass
        return None


# 全局单例
ocr_processor = OcrProcessor()
