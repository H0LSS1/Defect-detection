"""数据库初始化脚本: 建表(首次) + 插入种子数据(幂等, 可重复执行).

什么时候跑: 项目第一次搭好环境后手动执行一次; 之后重复跑也安全.
    conda/venv 环境: .venv\\Scripts\\python backend\\scripts\\init_db.py

做了三件事:
    1. 按 models/ 里的所有表模型, 在 MySQL 里建出全部 8 张表(create_all);
    2. 插入模型版本种子数据(yolov8n 登记) —— 任务创建时必须引用它;
    3. 插入 3 个焊缝缺陷类别占位(禁用状态, 换焊缝权重后再启用).
"""
from pathlib import Path
import sys

# 路径处理必须在"项目内 import"之前:
# 本文件在 backend/scripts/ 下, 不把 backend 加进 sys.path 的话
# import models 会直接 ModuleNotFoundError(踩过的坑).
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import models  # noqa: F401  import 包即触发全部表模型注册(见 models/__init__.py)
from models.base import Base
from models.defectclass import DefectClass
from models.modelversion import ModelVersion


# 连接串与 .env 保持一致(dev 环境固定值, 方便脚本独立运行)
url = "mysql+pymysql://root:defect123456@localhost:3306/defect_platform?charset=utf8mb4"
engine = create_engine(url, echo=True)  # echo=True: 打印每条实际执行的 SQL, 方便观察

# 按 Base 的全部子表建表.
# create_all 的特性: 表已存在就跳过(不会改表结构也不会清数据), 所以可重复执行.
Base.metadata.create_all(engine)


# 种子数据: 先查再插(幂等), 保证脚本跑一百遍也只有一条记录
with Session(engine) as session:
    # ① 模型版本: 任务创建时必须引用一条激活的记录
    if not session.query(ModelVersion).filter_by(modelname="yolov8n").first():
        session.add(ModelVersion(
            modelname="yolov8n",
            file_path="weights/yolov8n.pt",
            classess_count=80,
            input_size=640,
            is_active=True,
            remark="COCO 预训练权重",
        ))
    # ② 缺陷类别占位: 焊缝三大典型缺陷(禁用状态, 换焊缝权重后启用)
    for name, display in [("porosity", "气孔"), ("crack", "裂纹"), ("slag_inclusion", "夹渣")]:
        if not session.query(DefectClass).filter_by(class_name=name).first():
            session.add(DefectClass(class_name=name, display_name=display, is_enabled=False))
    session.commit()
