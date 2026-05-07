"""应用配置"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)


class Settings:
    # 数据库
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "tradedoc")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "root")

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    # OCR 引擎: auto / aliyun_api / local_model / mock
    OCR_ENGINE: str = os.getenv("OCR_ENGINE", "auto")
    OCR_MODEL_PATH: str = os.getenv("OCR_MODEL_PATH", "")
    OCR_CONFIDENCE_THRESHOLD: int = int(os.getenv("OCR_CONFIDENCE_THRESHOLD", "80"))

    # 阿里云 API
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")

    # 文件存储（与PHP共享）
    FILE_STORAGE_PATH: str = os.getenv("FILE_STORAGE_PATH", "")

    # 服务
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8100"))


settings = Settings()
