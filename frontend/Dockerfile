# ===== 前端镜像: 两段式构建(阶段1 编译, 阶段2 只留产物+nginx, 最终镜像很小) =====

# 阶段 1: Node 环境编译出 dist 静态文件
FROM node:20-alpine AS build
WORKDIR /app

# 先拷依赖清单安装(利用 Docker 层缓存: 源码改动不用重新 npm ci)
COPY package.json package-lock.json ./
RUN npm ci

# 拷源码并构建(vue-tsc 类型检查 + vite 打包)
COPY . .
RUN npm run build

# 阶段 2: nginx 托管静态文件
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
