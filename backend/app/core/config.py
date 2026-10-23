from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 配置来源声明
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # ===== 应用 =====
    app_name: str = "焊缝缺陷智能检测平台"
    app_env: str = "dev"
    debug: bool = True
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720

    # ===== MySQL =====
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "defect_platform"

    @property
    def mysql_url(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"

    # ===== Redis =====
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # ===== 文件存储（相对 backend/ 目录） =====
    upload_dir: str = "uploads"
    result_dir: str = "results"

    # ===== 模型 =====
    yolo_weights: str = "weights/yolov8n.pt"
    conf_threshold: float = 0.25


settings = Settings()
