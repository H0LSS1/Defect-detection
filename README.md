# 焊缝缺陷智能检测平台

一个基于 **FastAPI + Vue3 + YOLO** 的工业焊缝缺陷检测平台，覆盖 **图片上传 → 异步检测 → 可视化 → 报告导出** 完整业务流程，支持多用户与角色权限。

> 项目按"前后端分离 + 任务队列 + 容器化部署"的标准架构实现，适合作为全栈学习与二次开发的底子。

---

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [目录结构](#目录结构)
- [快速开始（Docker 部署，推荐）](#快速开始docker-部署推荐)
- [本地开发模式（前后端分别跑）](#本地开发模式前后端分别跑)
- [默认账号](#默认账号)
- [常用命令速查](#常用命令速查)
- [接口概览](#接口概览)
- [局域网访问](#局域网访问)
- [数据存在哪里](#数据存在哪里)
- [常见问题 FAQ](#常见问题-faq)
- [已知限制](#已知限制)

---

## 功能特性

| 模块 | 说明 |
|------|------|
| 用户认证 | JWT 登录态 + bcrypt 密码哈希 + admin/inspector 两级角色 |
| 用户管理 | admin 专属：用户列表、启用/禁用、角色调整（禁止操作自己） |
| 图像增强 | 算法集类 `ImageEnhancer`：中值/高斯/双边/非局部均值去噪、CLAHE、自适应伽马、USM 锐化、形态学等 16 种方法，生产管线取其中三种 |
| 目标检测 | YOLO 预训练权重（`.onnx` 部署，ONNX Runtime 推理），常驻内存单例，单图约 30ms |
| 异步任务 | Celery + Redis 队列；提交任务秒级返回任务号，后台逐张"增强→推理→标注→入库" |
| 进度查询 | Redis 实时进度 + MySQL 权威数据双源，前端轮询驱动进度条 |
| 可视化 | 原图/增强图/标注图三图对比，缺陷框坐标与置信度明细 |
| 统计看板 | ECharts：类别分布饼图、近 14 天趋势折线图、汇总卡片，支持按任务/类别筛选 |
| 报告导出 | python-docx 模板化 Word 报告：任务概览 + 类别统计 + 逐图标注图与框明细 |
| 部署 | 双阶段 Dockerfile + docker-compose 一键编排（数据库复用外部容器） |

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 |
| 异步任务 | Celery 5（Redis 作 broker/backend） |
| 数据库 | MySQL 8（8 张业务表）· Redis 7（队列/进度/缓存） |
| 检测模型 | Ultralytics YOLO 预训练权重（ONNX Runtime 推理） |
| 图像处理 | OpenCV · NumPy |
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Vue Router · Element Plus · ECharts · Axios |
| 部署 | Docker · docker-compose · Nginx |

## 系统架构

```
┌──────────────────┐   http://host:8080   ┌─────────────────────────┐
│     浏览器        │ ───────────────────▶ │  nginx 容器 (8080)       │
└──────────────────┘                      │  · 前端静态文件           │
                                          │  · /api  /media 反向代理  │
                                          └───────────┬─────────────┘
                                                      │
                             ┌────────────────────────▼───────────────────────┐
                             │  backend 容器 (FastAPI :8000, 不对外暴露)        │
                             │  认证 / 任务创建 / 进度 / 详情 / 统计 / 报告      │
                             └───────┬───────────────────────┬────────────────┘
                 send_task(消息入队)  │                       │ SQLAlchemy
                             ┌───────▼────────┐      ┌───────▼────────┐
                             │ Redis (队列/进度) │      │ MySQL (业务数据) │
                             └───────┬────────┘      └────────────────┘
                                     │ 取任务
                             ┌───────▼──────────────────────────────────────┐
                             │  worker 容器 (Celery)                         │
                             │  图像增强 → YOLO(ONNX) 推理 → 标注图 → 结果入库 │
                             └──────────────────────────────────────────────┘
```

## 目录结构

```
Defect/
├── backend/                  # 后端
│   ├── app/
│   │   ├── api/              # 路由层：auth(认证+用户管理) / tasks(任务) / stats(统计)
│   │   ├── core/             # 基础设施：config(.env) / db / security(JWT) / redis / celery_app
│   │   ├── schemas/          # Pydantic 模型(接口出入参)
│   │   ├── services/         # 业务层：enhance(增强) / detector(YOLO) / tasks_worker(异步) / report(报告)
│   │   └── main.py           # 应用入口(路由挂载/CORS/静态文件)
│   ├── models/               # SQLAlchemy 表模型(8 张表)
│   ├── check/                # 自检脚本：数据库连通/模型DDL/YOLO/ONNX基准/增强效果
│   ├── scripts/              # 运维脚本：init_db(建表+种子) / export_onnx
│   ├── weights/              # YOLO 权重(.pt/.onnx)【不入 git】
│   ├── uploads/ results/     # 上传原图 / 检测产物【不入 git】
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # 前端 (Vue3 + TypeScript)
│   ├── src/
│   │   ├── api/              # 类型定义 + axios 封装 + 接口函数
│   │   ├── stores/           # Pinia(登录态)
│   │   ├── router/           # 路由 + 登录守卫
│   │   ├── views/            # 7 个页面
│   │   └── ...
│   ├── nginx.conf            # 部署用 nginx 配置
│   └── Dockerfile
├── docker-compose.yml        # 一键编排(backend + worker + frontend)
├── PLAN.md                   # 项目全程计划与踩坑记录(未入库, 本地档案)
└── README.md
```

## 快速开始（Docker 部署，推荐）

### 环境要求

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)（建议设置开机自启）
- 项目根目录下存在 `backend/.env` 配置文件（内容见下）

### 步骤

```powershell
# 1. 启动数据库容器(首次)
docker run -d --name defect-mysql --restart unless-stopped -p 3306:3306 `
  -e MYSQL_ROOT_PASSWORD=defect123456 -e MYSQL_DATABASE=defect_platform `
  -e TZ=Asia/Shanghai -v defect-mysql-data:/var/lib/mysql `
  mysql:8.0 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

docker run -d --name defect-redis --restart unless-stopped -p 6379:6379 `
  -v defect-redis-data:/data redis:7-alpine redis-server --appendonly yes

# 2. 初始化数据库(建表 + 种子数据, 幂等可重复执行)
cd backend
..\.venv\Scripts\python scripts\init_db.py     # 新机器无 venv 时: 任意装了依赖的 Python 均可
cd ..

# 3. 构建镜像并启动(首次构建需下载依赖, 约 10~20 分钟)
docker compose up -d

# 4. 浏览器访问
http://localhost:8080
```

### `backend/.env` 配置说明

```ini
SECRET_KEY=任意长随机字符串        # JWT 签名密钥(必填, 泄露=任何人可伪造登录)
APP_NAME=焊缝缺陷智能检测平台
DEBUG=true

MYSQL_HOST=127.0.0.1              # Docker 部署时由 compose 覆盖为 host.docker.internal
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=defect123456
MYSQL_DATABASE=defect_platform

REDIS_HOST=127.0.0.1              # 同上, 部署时被覆盖
REDIS_PORT=6379
REDIS_DB=0

UPLOAD_DIR=uploads
RESULT_DIR=results
YOLO_WEIGHTS=weights/yolov8n.onnx # 推荐 onnx(比 pt 快一倍); 也可用 yolov8n.pt
CONF_THRESHOLD=0.25
```

### 首次使用

注册一个账号 → 用 admin 账号（见下）在"用户管理"里把它设为管理员/质检员 → 到**检测工作台**上传图片开始检测。

## 本地开发模式（前后端分别跑）

开发时改代码即时生效，比容器模式方便：

```powershell
# ── 终端 1: 后端(backend/ 目录) ──
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload     # API 在 8000, 文档 /docs

# ── 终端 2: Celery worker(backend/ 目录, 不跑它任务永远"排队中") ──
.venv\Scripts\python -m celery -A app.core.celery_app worker --loglevel=info --pool=solo

# ── 终端 3: 前端(frontend/ 目录) ──
npm install
npm run dev                                               # 页面在 5173, /api 自动代理到 8000
```

同样访问 `http://localhost:5173`。

## 默认账号

`init_db.py` 只建表和种子数据，不含账号。首次使用先在登录页**注册**，然后手动提权为管理员：

```sql
UPDATE users SET role='admin' WHERE username='你的用户名';
```

> 测试环境常用账号：`selftest_t2 / test12345`（admin）

## 常用命令速查

```powershell
docker compose up -d                            # 启动平台
docker compose down                             # 停止(数据不丢, 在宿主机目录/卷里)
docker compose logs -f worker                   # 盯检测后台日志
docker compose build && docker compose up -d    # 改代码后重建
docker start defect-mysql defect-redis          # 单独起数据库容器
```

## 接口概览

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /api/auth/register | 注册 | 公开 |
| POST | /api/auth/login | 登录(签发 JWT) | 公开 |
| GET | /api/auth/me | 当前用户信息 | 登录 |
| GET/PUT | /api/auth/users(/{id}) | 用户列表 / 启停与改角色 | admin |
| POST | /api/tasks | 创建检测任务(multipart 上传, 秒回任务号) | 登录 |
| GET | /api/tasks | 任务列表(admin 全量/他人仅本人) | 登录 |
| GET | /api/tasks/{task_no} | 任务详情(含图片与三图路径) | 登录+归属 |
| GET | /api/tasks/{task_no}/progress | 实时进度 | 登录+归属 |
| GET | /api/tasks/{task_no}/report | 导出 Word 检测报告 | 登录+归属 |
| GET | /api/stats/overview | 看板数据(支持 ?task_no=&class_name= 筛选) | 登录 |

完整定义见 `http://localhost:8080/docs`（Swagger，自动生成）。

## 局域网访问

部署机的 nginx 默认绑定所有网卡，局域网其他电脑直接访问 `http://<部署机IP>:8080` 即可。若无法访问，用**管理员 PowerShell** 放行防火墙：

```powershell
New-NetFirewallRule -DisplayName "defect-8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

## 数据存在哪里

| 数据 | 位置 | 说明 |
|------|------|------|
| 业务数据 | Docker 卷 `defect-mysql-data` | 账号/任务/检测结果 |
| 上传原图 | `backend/uploads/` | 宿主机目录 |
| 检测产物 | `backend/results/` | 增强图/标注图/报告，宿主机目录 |
| 模型权重 | `backend/weights/` | pt/onnx |

备份 = 拷贝这几个目录 + `mysqldump` 一次。迁移到新电脑的完整流程见 `PLAN.md`"阶段 7"。

## 常见问题 FAQ

<details>
<summary><b>1. 点击"创建任务"没反应，其他按钮也点不动？</b></summary>

前端组件渲染崩溃导致页面冻结。按 **F12 → Console** 看红色报错。已知原因：Element Plus 的 `on-change` 回调第一个参数是单个文件对象而非数组，误赋值给文件列表会引发此问题（本项目已修复，新代码勿再绑定 `:on-change`）。
</details>

<details>
<summary><b>2. 任务一直卡在"排队中"？</b></summary>

Celery worker 没启动。本地开发要开**第二个终端**跑 worker（见上文）；Docker 部署看 `docker compose logs worker`。
</details>

<details>
<summary><b>3. 容器内推理报 <code>operator torchvision::nms does not exist</code>？</b></summary>

torch 和 torchvision 版本错位（例如 CPU 版 torch 配 PyPI 版 torchvision）。两者必须**同源成对安装**，Dockerfile 已处理。
</details>

<details>
<summary><b>4. docker pull 拉不动镜像？</b></summary>

Docker Hub 直连不稳。可用镜像源拉取后改回标准名：

```powershell
docker pull docker.m.daocloud.io/library/python:3.12-slim
docker tag docker.m.daocloud.io/library/python:3.12-slim python:3.12-slim
```

pip 慢时加 `-i https://pypi.tuna.tsinghua.edu.cn/simple`。
</details>

<details>
<summary><b>5. Swagger 里上传文件字段变成文本框？</b></summary>

新版 FastAPI 输出 OpenAPI 3.1，旧版 Swagger UI 对文件字段渲染有缺陷（API 本身正常）。测试上传用 curl：

```powershell
curl.exe -X POST "http://localhost:8000/api/tasks" -H "Authorization: Bearer <token>" `
  -F "task_name=测试" -F "files=@图片1.jpg" -F "files=@图片2.jpg"
```
</details>

<details>
<summary><b>6. PowerShell 里执行 <code>.venv\Scripts\xxx</code> 报"无法加载模块"？</b></summary>

PowerShell 把 `.` 开头的路径当成特殊语法。写成 `.\.venv\Scripts\xxx` 或用绝对路径。
</details>

## 已知限制

1. **检测类别是 COCO 80 类**（person/bus 等），不是真正的焊缝缺陷（气孔/裂纹/夹渣）——项目约束为"直接使用 YOLO 预训练权重，不训练"。`defect_classes` 字典表已预留中文映射与颜色配置，换上焊缝权重即可无缝切换
2. 静态图片（`/media/*`）无鉴权，知道 URL 即可访问；正式环境应改为带 JWT 校验的流式接口
3. 单机部署（worker 为 `--pool=solo` 串行处理）；大规模并发需扩展 Celery worker 并引入任务去重
4. 后端镜像含完整 torch 依赖栈约 10GB；如需瘦身可固定 CPU 版 torch/torchvision 版本号并重试 CPU 源
5. 无自动化测试；`backend/check/` 下为手动冒烟脚本
