"""
TradeDoc Python 数据与AI服务 — FastAPI 入口

启动命令:
    python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8100 --reload
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ocr_router import router as ocr_router
from app.api.health_router import router as health_router

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# FastAPI 应用
app = FastAPI(
    title="TradeDoc Python Service",
    description="外贸文件智能管理系统 — OCR / NLP / 数据管道 / AI 推理服务",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router)
app.include_router(ocr_router)


@app.on_event("startup")
async def startup():
    logger.info("=" * 50)
    logger.info("TradeDoc Python Service 启动")
    logger.info("=" * 50)

    from app.services.ocr.engine import ocr_engine
    if ocr_engine.model_loaded:
        logger.info("OCR 引擎: Logics-Parsing-v2 [已加载]")
    else:
        logger.info("OCR 引擎: 模拟模式 (模型未安装)")


@app.get("/")
async def root():
    return {
        "service": "TradeDoc Python Service",
        "version": "1.0.0",
        "docs": "/docs",
    }
