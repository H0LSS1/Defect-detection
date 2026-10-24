"""模型公共基类: 所有表模型的"公共字段"都定义在这里, 子类自动继承.

什么是 ORM(Object-Relational Mapping, 对象关系映射)?
    简单说: 不写 SQL, 用 Python 类和对象操作数据库.
    一个类(class User)   对应一张表(users),
    一个对象(user 实例)  对应一行记录,
    一个属性(user.username) 对应一个字段.

SQLAlchemy 是 Python 最主流的 ORM 库; 本项目用它的 2.0 新式写法
(Mapped[类型] + mapped_column), 类型标注是必需品, 不是可有可无的装饰.
"""

from datetime import datetime

# DeclarativeBase: 声明式基类的基类; Mapped/mapped_column: 定义字段的新式写法
from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """所有表模型的共同父类.

    这里定义的三个字段会被每个子类表自动继承, 相当于给每张表
    都装上统一的"身份证(id)"和"时间戳(创建/更新时间)".

    注意: 直接把字段写在 DeclarativeBase 的子类上是可以的,
    SQLAlchemy 会把这些列拷贝到每一个子类表里.
    """

    # 主键: 每行的唯一编号, 自增(不用手动填, 数据库自动 +1)
    # BigInteger 编译成 MySQL 的 BIGINT, 比普通 INT 范围大, 防止数据量大了不够用
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # 创建时间: server_default=func.now() 表示由"数据库"在插入时自动填当前时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # 更新时间: onupdate=func.now() 表示走 ORM 更新这行时自动刷新时间
    # (注意: 只对通过 SQLAlchemy 的更新生效, 直接写 SQL UPDATE 不会触发)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
