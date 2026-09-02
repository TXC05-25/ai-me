FROM python:3.11-slim

WORKDIR /app

# 系统依赖（curl 用于健康检查 + 构建 pymilvus 需要编译工具）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（先单独 copy 缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 代码
COPY backend/ /app/backend/

# 数据持久化目录（HF Spaces 重启会丢，建议后续接外部存储）
RUN mkdir -p /app/backend/vector_db /app/backend/logs

# HF Spaces 默认端口是 7860
ENV APP_PORT=7860
ENV APP_HOST=0.0.0.0

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

EXPOSE 7860

# 启动时自动构建向量库（首次启动慢一些，后续从持久化目录恢复）
CMD ["sh", "-c", "python backend/main.py"]