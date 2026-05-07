"""健康检查路由"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import HealthResponse
from app.services.ocr.engine import ocr_engine

router = APIRouter(tags=["Health"])


@router.get("/api/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """服务健康检查"""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        ocr_engine="logics_parsing_v2",
        ocr_model_loaded=ocr_engine.model_loaded,
        db_connected=db_ok,
    )
