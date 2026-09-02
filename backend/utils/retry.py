"""
失败重试装饰器（指数退避）
"""

from __future__ import annotations

import asyncio
from functools import wraps
from typing import Callable

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

logging.basicConfig(level=logging.INFO)
_std_log = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
    retry_on: tuple = (Exception,),
):
    """指数退避重试装饰器

    Args:
        max_attempts: 最大尝试次数
        min_wait: 最小等待秒数
        max_wait: 最大等待秒数
        retry_on: 触发重试的异常类型
    """
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                @retry(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(multiplier=min_wait, max=max_wait),
                    retry=retry_if_exception_type(retry_on),
                    before_sleep=before_sleep_log(_std_log, logging.WARNING),
                    reraise=True,
                )
                async def _inner():
                    return await func(*args, **kwargs)
                return await _inner()
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                @retry(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(multiplier=min_wait, max=max_wait),
                    retry=retry_if_exception_type(retry_on),
                    before_sleep=before_sleep_log(_std_log, logging.WARNING),
                    reraise=True,
                )
                def _inner():
                    return func(*args, **kwargs)
                return _inner()
            return sync_wrapper
    return decorator