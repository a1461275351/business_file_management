# TradeDoc Python 数据与AI服务 — 目录结构说明

## 技术栈
- Python 3.10+
- FastAPI（HTTP API 服务）
- PaddleOCR（OCR 引擎）
- Pandas + HanLP（数据处理 / NLP）
- Redis（任务消费）
- MySQL（共享数据库）

## 目录结构

```
tradedoc-python/
├── app/
│   ├── api/                          # FastAPI 路由
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── ocr_router.py             # OCR 识别接口
│   │   ├── nlp_router.py             # NLP 字段提取接口
│   │   ├── pipeline_router.py        # 数据管道接口
│   │   ├── model_router.py           # 大模型推理接口（三期）
│   │   └── health_router.py          # 健康检查接口
│   ├── services/                     # 业务逻辑
│   │   ├── ocr/
│   │   │   ├── __init__.py
│   │   │   ├── ocr_engine.py         # PaddleOCR 封装
│   │   │   ├── image_preprocess.py   # 图片预处理（去噪/旋转/增强）
│   │   │   ├── pdf_converter.py      # PDF 转图片
│   │   │   └── language_detect.py    # 语种自动检测
│   │   ├── nlp/
│   │   │   ├── __init__.py
│   │   │   ├── field_extractor.py    # 字段结构化提取
│   │   │   ├── template_matcher.py   # 按文件类型模板匹配字段
│   │   │   ├── entity_recognizer.py  # 命名实体识别（公司名/金额/日期）
│   │   │   └── confidence_scorer.py  # 置信度评分
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── data_cleaner.py       # 数据清洗（格式标准化/去重/校验）
│   │   │   ├── currency_converter.py # 币种换算
│   │   │   ├── cross_checker.py      # 跨文件一致性校验
│   │   │   ├── hs_code_validator.py  # HS 编码合法性校验
│   │   │   └── warehouse_writer.py   # 结构化数据入库
│   │   └── model/                    # 三期：大模型
│   │       ├── __init__.py
│   │       ├── chat_service.py       # 业务问答推理
│   │       ├── rag_service.py        # RAG 检索增强
│   │       └── training_pipeline.py  # 模型微调数据准备
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               # 配置管理（读取环境变量/.env）
│   ├── models/                       # SQLAlchemy/Pydantic 模型
│   │   ├── __init__.py
│   │   ├── database.py               # MySQL 连接
│   │   ├── schemas.py                # Pydantic 请求/响应模型
│   │   └── db_models.py              # SQLAlchemy ORM 模型
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py             # 文件读取/路径处理
│       ├── redis_client.py           # Redis 连接
│       └── logger.py                 # 日志配置
├── tests/                            # 测试
│   ├── test_ocr.py
│   ├── test_nlp.py
│   └── test_pipeline.py
├── scripts/                          # 运维脚本
│   ├── start_api.sh                  # 启动 FastAPI 服务
│   ├── start_worker.sh               # 启动队列消费 Worker
│   └── init_paddleocr.py             # 首次下载 PaddleOCR 模型
├── requirements/
│   ├── base.txt                      # 基础依赖
│   ├── ocr.txt                       # OCR 相关依赖
│   └── model.txt                     # 大模型相关依赖（三期）
├── .env.example                      # 环境变量模板
├── Dockerfile                        # Docker 构建（可选）
└── README_STRUCTURE.md               # 本文件
```

## API 接口设计

### OCR 识别
```
POST /api/ocr/recognize
  Body: { document_id, file_path, document_type_code, language }
  Response: { task_id, status }
```

### 字段提取
```
POST /api/nlp/extract-fields
  Body: { document_id, ocr_text, document_type_code }
  Response: { fields: [{field_key, value, confidence, bbox}] }
```

### 数据清洗
```
POST /api/pipeline/clean
  Body: { document_id }
  Response: { cleaned_fields_count, warnings }
```

### 跨文件校验
```
POST /api/pipeline/cross-check
  Body: { order_id }
  Response: { alerts: [{type, description, severity}] }
```

### 大模型问答（三期）
```
POST /api/model/chat
  Body: { question, user_id, context_limit }
  Response: { answer, sources: [{doc_no, field}] }
```

### 健康检查
```
GET /api/health
  Response: { status: "ok", ocr_engine: "ready", db: "connected" }
```

## 队列消费模式

Python 同时支持两种工作模式：

1. **HTTP 同步调用**：PHP 通过 HTTP 请求调用 FastAPI 接口，适用于实时性要求高的场景
2. **Redis 队列消费**：Python Worker 监听 Redis 队列，消费 OCR 等耗时任务

```python
# Worker 伪代码
while True:
    task = redis.brpop('tradedoc:ocr_queue')
    process_ocr(task)
    update_mysql(task.document_id, result)
    redis.publish('tradedoc:notifications', notification)
```

## 依赖清单 (requirements/base.txt)

```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0
pymysql>=1.1.0
redis>=5.0
pydantic>=2.5
python-dotenv>=1.0
paddleocr>=2.7
paddlepaddle>=2.5
Pillow>=10.0
pdf2image>=1.16
pandas>=2.1
numpy>=1.26
```
