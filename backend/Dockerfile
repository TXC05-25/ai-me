FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
# 构建上下文是项目根目录（docker-compose.yml 里 context: .），
# 所以 requirements.txt 在根目录而不是 backend/ 下
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 代码
COPY backend/ /app/backend/

# 数据持久化目录
RUN mkdir -p /app/backend/vector_db /app/backend/logs

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# 必须切到 backend/ 目录再启动，否则 main.py 里的
# `from config import ...` 会因为找不到模块而启动失败
WORKDIR /app/backend
CMD ["python", "main.py"]