"""
简单的内存限流器（基于滑动窗口）
===================================
生产建议替换为 Redis 实现。
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    def __init__(self, max_per_minute: int = 30):
        self.max_per_minute = max_per_minute
        self._records: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        """检查 key 在当前窗口内是否允许请求"""
        now = time.time()
        with self._lock:
            window = self._records[key]
            # 清理 60s 之前的记录
            while window and window[0] < now - 60:
                window.popleft()
            if len(window) >= self.max_per_minute:
                return False
            window.append(now)
            return True

    def remaining(self, key: str) -> int:
        """当前 key 剩余可用请求数"""
        now = time.time()
        with self._lock:
            window = self._records[key]
            while window and window[0] < now - 60:
                window.popleft()
            return max(0, self.max_per_minute - len(window))