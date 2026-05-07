"""OCR 相关 API 路由"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import OcrRequest, OcrResponse
from app.services.ocr.processor import ocr_processor
from app.services.ocr.engine import ocr_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ocr", tags=["OCR"])


@router.post("/process", response_model=None)
async def process_ocr_task(request: OcrRequest, db: Session = Depends(get_db)):
    """
    处理 OCR 任务（由 PHP 调用）

    PHP 上传文件后创建 ocr_task，然后调用此接口触发处理
    """
    # 找到该文件的待处理任务
    task = db.execute(
        text("SELECT id FROM ocr_tasks WHERE document_id = :doc_id "
             "AND status IN ('pending', 'retry') ORDER BY id DESC LIMIT 1"),
        {"doc_id": request.document_id}
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="没有待处理的 OCR 任务")

    result = ocr_processor.process_task(db, task[0])

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "OCR 处理失败"))

    return result


@router.post("/process-by-task/{task_id}")
async def process_by_task_id(task_id: int, db: Session = Depends(get_db)):
    """按任务ID处理"""
    result = ocr_processor.process_task(db, task_id)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "处理失败"))

    return result


@router.get("/pending-tasks")
async def list_pending_tasks(db: Session = Depends(get_db)):
    """查看待处理的 OCR 任务队列"""
    tasks = db.execute(
        text("SELECT t.id, t.document_id, t.task_type, t.status, t.priority, "
             "t.created_at, d.doc_no, d.original_filename, dt.name as type_name "
             "FROM ocr_tasks t "
             "JOIN documents d ON t.document_id = d.id "
             "JOIN document_types dt ON d.document_type_id = dt.id "
             "WHERE t.status IN ('pending', 'retry') "
             "ORDER BY t.priority ASC, t.created_at ASC "
             "LIMIT 50")
    ).mappings().all()

    return {"data": [dict(t) for t in tasks]}


@router.post("/process-all-pending")
async def process_all_pending(db: Session = Depends(get_db)):
    """批量处理所有待处理任务"""
    tasks = db.execute(
        text("SELECT id FROM ocr_tasks WHERE status IN ('pending', 'retry') "
             "ORDER BY priority ASC, created_at ASC LIMIT 20")
    ).all()

    results = []
    for task in tasks:
        result = ocr_processor.process_task(db, task[0])
        results.append(result)

    success_count = sum(1 for r in results if r.get("success"))
    return {
        "message": f"处理完成: {success_count}/{len(results)} 成功",
        "results": results,
    }


@router.get("/cache/{document_id}")
async def get_ocr_cache(document_id: int):
    """
    获取文件的 OCR 缓存结果（数据库缓存，3天有效）
    """
    data = ocr_processor.get_cache(document_id)

    if not data:
        return {"cached": False, "data": None}

    # 返回字段 map，方便前端匹配
    field_map = {}
    for f in data.get("fields", []):
        field_map[f["field_key"]] = {
            "value": f.get("field_value", ""),
            "confidence": f.get("confidence", 0),
        }
    return {"cached": True, "data": field_map}


@router.get("/engine-status")
async def engine_status():
    """OCR 引擎状态"""
    return {
        "engine_mode": ocr_engine.engine_mode,
        "api_key_set": bool(ocr_engine.api_key),
        "model_loaded": ocr_engine.model_loaded,
        "model_path": ocr_engine.model_path,
        "mode": "production" if ocr_engine.model_loaded else "mock",
    }
