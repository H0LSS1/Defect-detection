from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine
from models.base import Base
from sqlalchemy.orm import Session
from models.modelversion import ModelVersion
from models.defectclass import DefectClass
import models


url = "mysql+pymysql://root:defect123456@localhost:3306/defect_platform?charset=utf8mb4"
engine = create_engine(url, echo=True)


Base.metadata.create_all(engine)


with Session(engine) as session:
    if not session.query(ModelVersion).filter_by(modelname="yolov8n").first():
        session.add(ModelVersion(
            modelname="yolov8n",
            file_path="weights/yolov8n.pt",
            classess_count=80,
            input_size=640,
            is_active=True,
            remark="COCO 预训练权重",
        ))
    # defect_classes 插 3 个焊缝类别占位（is_enabled=False，等以后换焊缝权重再启用）
    for name, display in [("porosity", "气孔"), ("crack", "裂纹"), ("slag_inclusion", "夹渣")]:
        if not session.query(DefectClass).filter_by(class_name=name).first():
            session.add(DefectClass(class_name=name, display_name=display, is_enabled=False))
    session.commit()