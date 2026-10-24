"""全局配置模块: 把 backend/.env 文件里的配置项读进 Python, 全项目共用.

其他任何文件需要用到数据库地址、密钥、路径等配置时, 都这样取:
    from app.core.config import settings
    settings.mysql_url

为什么这么做:
    1. 配置写死在代码里, 换一台机器/换一组密码就要改代码, 容易漏改出 bug;
    2. .env 文件已被 .gitignore 排除, 密码等敏感信息不会被提交到 git 仓库.
"""

from pathlib import Path

# pydantic-settings 是 pydantic 的扩展, 专门用来"从 .env / 环境变量 读配置"
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """配置类: 每个属性对应 .env 里的一个配置项.

    核心规则(也是 pydantic-settings 的魔法):
      - 类属性名 与 .env 里的 KEY 大小写不敏感地一一对应
        (代码里写 mysql_host, .env 里写 MYSQL_HOST, 两者自动匹配)
      - 属性必须带类型标注(如 : str), 否则 pydantic 不认为它是配置字段
      - 有默认值的字段可缺省; 无默认值的字段(如 secret_key)是必填,
        .env 里缺了会在启动时直接报错 —— 防止带着错误配置悄悄跑起来
    """

    # model_config 是 pydantic 的"类级配置开关", 固定写法.
    # env_file: 指定 .env 文件的位置.
    #   本文件在 backend/app/core/ 下, parents 的层级是:
    #   parents[0]=core  parents[1]=app  parents[2]=backend
    #   所以 parents[2] / ".env" 就是 backend/.env
    # extra="ignore": .env 里如果出现了类里没定义的 KEY, 不报错直接忽略
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ===== 应用基础信息 =====
    app_name: str = "焊缝缺陷智能检测平台"   # 显示在 Swagger 文档页面标题
    app_env: str = "dev"                     # dev / prod, 标识当前运行环境
    debug: bool = True                       # True 时报错信息更详细

    # ===== JWT 认证 =====
    # secret_key: 给 token 签名的密钥, 只存在 .env 里, 代码中无默认值(必填).
    #             泄露这个 = 别人可以伪造任意用户的登录凭证.
    secret_key: str
    jwt_algorithm: str = "HS256"             # 签名算法, HS256 是最常用的对称加密算法
    access_token_expire_minutes: int = 720   # token 有效期(分钟), 720 = 12 小时

    # ===== MySQL 连接信息(与 docker 里的 defect-mysql 容器一致) =====
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""                 # 敏感信息, 实际值从 .env 读
    mysql_database: str = "defect_platform"

    # ===== Redis 连接信息(与 docker 里的 defect-redis 容器一致) =====
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = ""                 # 空字符串 = 无密码
    redis_db: int = 0                        # Redis 有 16 个独立小库(0~15), 业务用 0 号

    # ===== 文件存储目录(相对 backend/ 目录) =====
    upload_dir: str = "uploads"              # 用户上传的原始图
    result_dir: str = "results"              # 检测产物: 增强图/标注图/报告

    # ===== 检测模型 =====
    yolo_weights: str = "weights/yolov8n.pt"  # 权重路径, 可改成 .onnx 切换推理后端
    conf_threshold: float = 0.25              # 默认置信度阈值: 低于它的检测框直接丢弃

    @property
    def mysql_url(self) -> str:
        """派生配置: 把零散的连接参数拼成 SQLAlchemy 认识的连接串.

        @property 表示"像属性一样访问的方法", 调用时不加括号:
            settings.mysql_url    (正确)
            settings.mysql_url()  (错误! 它不是普通方法)
        格式解读: mysql+pymysql://用户名:密码@主机:端口/库名?charset=utf8mb4
                  └驱动┘└────────── SQLAlchemy 通过 pymysql 驱动连 MySQL ──────────┘
        """
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )


# 模块级单例: 本模块被 import 时就创建好唯一的 settings 对象.
# 全项目任何地方 import 它, 拿到的都是同一个实例(.env 只会被读一次).
settings = Settings()
