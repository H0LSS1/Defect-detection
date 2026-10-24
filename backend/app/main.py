"""FastAPI 应用入口: 创建 app 实例, 把所有路由和静态文件服务挂载进来.

启动方式(在 backend/ 目录下):
    .venv\\Scripts\\python -m uvicorn app.main:app --reload
启动后:
    http://127.0.0.1:8000/docs      → Swagger 接口文档(自动生成)
    http://127.0.0.1:8000/media/... → 静态图片直链
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.api.stats import router as stats_router

# 创建应用实例: title 显示在 Swagger 页面上
app = FastAPI(title=settings.app_name)

# CORS 中间件: 浏览器的安全策略规定, 网页只能请求"同源"的接口.
# 开发时前端(5173端口)和后端(8000端口)是不同源, 不加这个中间件浏览器会拒绝请求.
# allow_origins 里写前端地址; 正式部署后改成实际域名.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端 Vite 默认地址，阶段 6 会用到
    allow_credentials=True,
    allow_methods=["*"],      # 放行所有 HTTP 方法(GET/POST/...)
    allow_headers=["*"],      # 放行所有请求头(含 Authorization)
)

# 挂载各模块路由: 每个路由文件一个 include, 各接口自动带上各自的前缀
app.include_router(auth_router)    # /api/auth/*
app.include_router(tasks_router)   # /api/tasks/*
app.include_router(stats_router)   # /api/stats/*

# 静态文件服务: 让前端能用 <img src="http://host:8000/media/results/...">
# 直接展示服务器上的图片, 而不用为每张图写接口.
# 注意: StaticFiles 没有鉴权, 任何知道 URL 的人都能看图 ——
# 学习项目可接受; 正式环境应改成带 JWT 校验的流式接口.
BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/ 目录
uploads_dir = BACKEND_DIR / settings.upload_dir    # backend/uploads
results_dir = BACKEND_DIR / settings.result_dir    # backend/results
uploads_dir.mkdir(exist_ok=True)  # 目录必须已存在, StaticFiles 才能挂载
results_dir.mkdir(exist_ok=True)
app.mount("/media/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
app.mount("/media/results", StaticFiles(directory=str(results_dir)), name="results")
