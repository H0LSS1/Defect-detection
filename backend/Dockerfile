# ===== 后端镜像: Python 3.12 精简底座 =====
FROM python:3.12-slim

WORKDIR /app

# opencv 运行需要的系统库(libGL); 装完清缓存减小镜像体积
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 先只拷依赖清单再安装: 代码改动时这一层走缓存, 不用重新下载依赖
COPY requirements.txt .

# 容器里没有 GPU, 单独先装 CPU 版 PyTorch(约 200MB),
# 否则 ultralytics 的依赖解析会拉取带 CUDA 的版本(好几个 GB).
# torch 和 torchvision 必须同源成对安装 —— 混用 CPU 版 torch + PyPI 版 torchvision
# 会报 "operator torchvision::nms does not exist"(版本错位, 踩过的坑).
# -i 清华源: 国内网络直连 pypi 官方源慢/不稳
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    || pip install --no-cache-dir torch torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装其余依赖(fastapi/celery/opencv/onnxruntime...)
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝代码(weights/uploads/results/.env 已被 .dockerignore 排除,
# 由 docker-compose 的 volumes 挂载和环境变量注入)
COPY . .

EXPOSE 8000

# 容器内必须监听 0.0.0.0(默认 127.0.0.1 只收容器内部请求, 外部访问不到)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
