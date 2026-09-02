"""
性能指标采集：每个节点的耗时 + 滑动窗口 P50 / P95 / P99
=========================================================
借鉴自 Kushal9889/kushal-portfolio-v2 的核心理念：
「每个延迟数字都经过测量，不在 README 里拍脑袋」
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional


@dataclass
class TimingSample:
    """单次请求的各阶段耗时"""
    timestamp: float
    intent_ms: float = 0.0
    rewrite_ms: float = 0.0
    retrieve_ms: float = 0.0
    rerank_ms: float = 0.0
    assemble_ms: float = 0.0
    generate_ms: float = 0.0
    total_ms: float = 0.0
    first_token_ms: Optional[float] = None
    token_count: int = 0


class MetricsCollector:
    """滑动窗口指标收集器（默认保留最近 200 条）"""

    def __init__(self, window_size: int = 200):
        self.window_size = window_size
        self._samples: deque[TimingSample] = deque(maxlen=window_size)
        self._lock = Lock()
        # 全局计数器
        self._total_requests = 0
        self._total_tokens = 0

    def record(self, sample: TimingSample) -> None:
        with self._lock:
            self._samples.append(sample)
            self._total_requests += 1
            self._total_tokens += sample.token_count

    @property
    def total_requests(self) -> int:
        return int(self._total_requests)

    @property
    def total_tokens(self) -> int:
        return int(self._total_tokens)

    def _percentile(self, values: list[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_v = sorted(values)
        idx = min(int(len(sorted_v) * p), len(sorted_v) - 1)
        return round(sorted_v[idx], 1)

    def summary(self) -> dict:
        """汇总指标：P50 / P95 / P99"""
        with self._lock:
            samples = list(self._samples)

        if not samples:
            return {
                "total_requests": self._total_requests,
                "total_tokens": self._total_tokens,
                "window_size": 0,
                "ttft_ms": {"p50": 0, "p95": 0, "p99": 0},
                "total_ms": {"p50": 0, "p95": 0, "p99": 0},
                "per_stage_ms": {
                    "intent": {"p50": 0, "p95": 0, "p99": 0},
                    "rewrite": {"p50": 0, "p95": 0, "p99": 0},
                    "retrieve": {"p50": 0, "p95": 0, "p99": 0},
                    "rerank": {"p50": 0, "p95": 0, "p99": 0},
                    "assemble": {"p50": 0, "p95": 0, "p99": 0},
                    "generate": {"p50": 0, "p95": 0, "p99": 0},
                },
                "tokens_per_sec": 0.0,
            }

        def stage(stage_attr: str) -> dict:
            vals = [getattr(s, stage_attr) for s in samples if getattr(s, stage_attr) > 0]
            return {
                "p50": self._percentile(vals, 0.5),
                "p95": self._percentile(vals, 0.95),
                "p99": self._percentile(vals, 0.99),
            }

        ttft_vals = [s.first_token_ms for s in samples if s.first_token_ms]
        total_vals = [s.total_ms for s in samples]
        # tokens/s 估算（generate 阶段产出速率）
        gen_vals = [(s.token_count, s.generate_ms) for s in samples if s.generate_ms > 0 and s.token_count > 0]
        avg_tps = sum(t / (g / 1000) for t, g in gen_vals) / len(gen_vals) if gen_vals else 0.0

        return {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "window_size": len(samples),
            "ttft_ms": {
                "p50": self._percentile(ttft_vals, 0.5),
                "p95": self._percentile(ttft_vals, 0.95),
                "p99": self._percentile(ttft_vals, 0.99),
            },
            "total_ms": {
                "p50": self._percentile(total_vals, 0.5),
                "p95": self._percentile(total_vals, 0.95),
                "p99": self._percentile(total_vals, 0.99),
            },
            "per_stage_ms": {
                "intent": stage("intent_ms"),
                "rewrite": stage("rewrite_ms"),
                "retrieve": stage("retrieve_ms"),
                "rerank": stage("rerank_ms"),
                "assemble": stage("assemble_ms"),
                "generate": stage("generate_ms"),
            },
            "tokens_per_sec": round(avg_tps, 1),
        }


# 单例
metrics_collector = MetricsCollector()


class StageTimer:
    """节点级计时器（context manager）"""

    def __init__(self, sample: TimingSample, stage: str):
        self.sample = sample
        self.stage = stage

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.perf_counter() - self._start) * 1000
        setattr(self.sample, f"{self.stage}_ms", round(elapsed, 1))


def new_sample() -> TimingSample:
    """创建新的计时样本（应在请求开始时调用）"""
    return TimingSample(timestamp=time.time())