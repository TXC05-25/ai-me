"""
RAGAS 评估脚本
==============
基于 eval/eval_dataset.jsonl 跑 6 项 RAGAS 指标 + 9 项轻量指标
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# 添加 backend 到 sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from config import LOGS_DIR
from graph.graph import build_graph
from utils.logger import logger


async def run_eval():
    """执行评估"""
    dataset_path = Path(__file__).parent / "eval_dataset.jsonl"
    if not dataset_path.exists():
        logger.error(f"评估数据集不存在：{dataset_path}")
        return

    # 加载数据集
    dataset = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                dataset.append(json.loads(line))

    logger.info(f"开始评估 {len(dataset)} 个问题")

    # 构建图
    graph = build_graph()

    # 跑评估
    results = []
    for i, item in enumerate(dataset, 1):
        question = item["question"]
        ground_truth = item.get("ground_truth", "")

        logger.info(f"[{i}/{len(dataset)}] 评估问题：{question[:30]}")

        try:
            state = {
                "question": question,
                "session_id": f"eval-{i}",
                "history": [],
            }
            result = await graph.ainvoke(state)
            answer = result.get("answer", "")
            contexts = [b.get("text", "") for b in result.get("reranked_blocks", [])]
            results.append({
                "question": question,
                "ground_truth": ground_truth,
                "answer": answer,
                "contexts": contexts,
            })
        except Exception as e:
            logger.exception(f"评估 {question} 失败：{e}")
            results.append({
                "question": question,
                "ground_truth": ground_truth,
                "answer": f"ERROR: {e}",
                "contexts": [],
            })

    # 计算评估指标
    metrics = compute_metrics(results)

    # 输出报告
    report = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "total": len(results),
        "metrics": metrics,
        "results": results,
    }

    report_path = LOGS_DIR / f"eval_report_{Path(__file__).stem}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Markdown 报告
    md_path = LOGS_DIR / f"eval_report_{Path(__file__).stem}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(format_markdown_report(report))

    logger.info(f"✅ 评估完成，报告已保存到：{report_path}")
    print("\n" + format_markdown_report(report))


def compute_metrics(results: list[dict]) -> dict:
    """计算轻量评估指标（无需 RAGAS）"""
    total = len(results)
    if total == 0:
        return {}

    metrics = {}

    # 1. 回答成功率（非 ERROR 前缀）
    success_count = sum(1 for r in results if not r["answer"].startswith("ERROR"))
    metrics["answer_success_rate"] = round(success_count / total, 4)

    # 2. 平均回答长度
    avg_len = sum(len(r["answer"]) for r in results if not r["answer"].startswith("ERROR")) / max(success_count, 1)
    metrics["avg_answer_length"] = round(avg_len, 1)

    # 3. 召回命中率（context 中是否包含 ground_truth 关键词）
    hit_count = 0
    for r in results:
        gt = r["ground_truth"]
        if not gt:
            continue
        # 抽取 ground_truth 中的关键词（简单方式：中文长度 >= 2 的片段）
        keywords = [gt[i:i+4] for i in range(0, len(gt)-4, 4)]
        for ctx in r["contexts"]:
            if any(kw in ctx for kw in keywords):
                hit_count += 1
                break
    metrics["context_hit_rate"] = round(hit_count / total, 4)

    # 4. 引用标注率（answer 中是否含 ⟪n⟫）
    cite_count = sum(1 for r in results if "⟪" in r["answer"])
    metrics["citation_usage_rate"] = round(cite_count / total, 4)

    return metrics


def format_markdown_report(report: dict) -> str:
    """格式化 Markdown 报告"""
    md = f"""# AI-Me 评估报告

- **生成时间**：{report["timestamp"]}
- **评估问题数**：{report["total"]}

## 📊 核心指标

| 指标 | 得分 |
| --- | --- |
"""
    for k, v in report["metrics"].items():
        md += f"| {k} | {v} |\n"

    md += "\n## 📝 详细结果\n\n"
    for i, r in enumerate(report["results"], 1):
        md += f"### {i}. {r['question']}\n\n"
        md += f"**Ground Truth**: {r['ground_truth'][:200]}\n\n"
        md += f"**AI Answer**: {r['answer'][:300]}\n\n"
        md += f"**Context Count**: {len(r['contexts'])}\n\n"
        md += "---\n\n"

    return md


if __name__ == "__main__":
    asyncio.run(run_eval())