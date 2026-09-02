"""
日志模块：全局日志 + 请求级日志
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from config import LOGS_DIR

# 日志格式
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# 移除默认 handler
logger.remove()

# 控制台
logger.add(sys.stderr, format=LOG_FORMAT, level="INFO", colorize=True)

# 全局应用日志（enqueue=False 避免 Windows multiprocessing 权限问题）
logger.add(
    LOGS_DIR / "app.log",
    format=LOG_FORMAT,
    level="INFO",
    rotation="100 MB",
    retention="30 days",
    encoding="utf-8",
    enqueue=False,
)

# 请求级日志
logger.add(
    LOGS_DIR / "requests.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="100 MB",
    retention="30 days",
    encoding="utf-8",
    enqueue=False,
    filter=lambda record: "REQUEST" in record["message"] or "CHAT" in record["message"],
)


# 别名
request_logger = logger.bind(module="request")
node_logger = logger.bind(module="node")


def setup_logger():
    logger.info("日志系统初始化完成")