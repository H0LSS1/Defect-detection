"""Model sanity check: import models, compile MySQL DDL, catch type/length errors without touching DB."""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

import models.user  # noqa: F401  触发模型注册，后续新增模型在此追加
import models.modelversion  # noqa: F401  触发模型注册，后续新增模型在此追加
import models.defectclass  # noqa: F401  触发模型注册，后续新增模型在此追加
import models.task  # noqa: F401  触发模型注册，后续新增模型在此追加
import models.image  # noqa: F401  触发模型注册，后续新增模型在此追加
import models.detectionresult  # noqa: F401  触发模型注册，后续新增模型在此追加
import models.report  # noqa: F401  触发模型注册，后续新增模型在此追加
import models.operationlog  # noqa: F401  触发模型注册，后续新增模型在此追加
from models.base import Base


def main() -> int:
    failures = []
    for table in Base.metadata.sorted_tables:
        print(f"--- table: {table.name}")
        try:
            ddl = str(CreateTable(table).compile(dialect=mysql.dialect()))
            print(ddl.strip())
        except Exception as exc:
            failures.append(table.name)
            print(f"[FAIL] {table.name}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"[FAIL] DDL compile failed: {', '.join(failures)}")
        return 1
    print("[PASS] all models compile to MySQL DDL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
