"""基准测试套件：标准数据集 + A/B 测试 + 性能对比."""

from __future__ import annotations

import time
import json
import math
import statistics
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Sequence

from .metrics import MetricSuite, MetricResult


# 模型生成函数：(query, contexts) -> response
GenerateFn = Callable[[str, List[str]], str]


@dataclass
class BenchmarkCase:
    case_id: str
    query: str
    contexts: List[str] = field(default_factory=list)
    ground_truth: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def make(cls, query: str, ground_truth: str = "",
             contexts: Optional[List[str]] = None, **metadata) -> "BenchmarkCase":
        return cls(
            case_id=metadata.pop("case_id", f"case_{uuid.uuid4().hex[:8]}"),
            query=query,
            contexts=contexts or [],
            ground_truth=ground_truth,
            metadata=metadata,
        )


@dataclass
class CaseResult:
    case_id: str
    query: str
    response: str
    latency_ms: float
    metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    aggregate_score: float = 0.0
    passed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "query": self.query,
            "response_preview": self.response[:200],
            "latency_ms": round(self.latency_ms, 2),
            "metrics": self.metrics,
            "aggregate_score": round(self.aggregate_score, 4),
            "passed": self.passed,
        }


@dataclass
class BenchmarkResult:
    benchmark_id: str
    name: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    avg_score: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    metric_averages: Dict[str, float]
    case_results: List[CaseResult]
    duration_s: float

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["case_results"] = [c.to_dict() for c in self.case_results]
        return d

    def summary(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "name": self.name,
            "total_cases": self.total_cases,
            "pass_rate": round(self.pass_rate, 4),
            "avg_score": round(self.avg_score, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "metric_averages": {k: round(v, 4) for k, v in self.metric_averages.items()},
        }


class Benchmark:
    """基准测试运行器."""

    def __init__(self, name: str, cases: Optional[List[BenchmarkCase]] = None,
                 metric_suite: Optional[MetricSuite] = None,
                 pass_threshold: float = 0.7):
        self.name = name
        self.cases = cases or []
        self.metric_suite = metric_suite or MetricSuite()
        self.pass_threshold = pass_threshold

    def add_case(self, case: BenchmarkCase) -> "Benchmark":
        self.cases.append(case)
        return self

    @classmethod
    def from_jsonl(cls, name: str, path: str,
                    metric_suite: Optional[MetricSuite] = None) -> "Benchmark":
        cases = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                cases.append(BenchmarkCase(
                    case_id=obj.get("case_id") or f"case_{len(cases)}",
                    query=obj["query"],
                    contexts=obj.get("contexts", []),
                    ground_truth=obj.get("ground_truth", ""),
                    metadata=obj.get("metadata", {}),
                ))
        return cls(name=name, cases=cases, metric_suite=metric_suite)

    @classmethod
    def standard_qa(cls) -> "Benchmark":
        """内置标准 QA 数据集示例。"""
        return cls(name="standard_qa", cases=[
            BenchmarkCase.make(
                query="What is the capital of France?",
                ground_truth="Paris",
                contexts=["Paris is the capital and most populous city of France."],
            ),
            BenchmarkCase.make(
                query="Who wrote Hamlet?",
                ground_truth="William Shakespeare",
                contexts=["Hamlet is a tragedy written by William Shakespeare around 1600."],
            ),
            BenchmarkCase.make(
                query="What is photosynthesis?",
                ground_truth="The process by which plants convert light into chemical energy.",
                contexts=["Photosynthesis is the process used by plants and other organisms "
                          "to convert light energy into chemical energy."],
            ),
        ])

    def run(self, generate_fn: GenerateFn) -> BenchmarkResult:
        start = time.time()
        case_results: List[CaseResult] = []
        latencies: List[float] = []
        metric_sums: Dict[str, float] = {}
        metric_counts: Dict[str, int] = {}

        for case in self.cases:
            t0 = time.time()
            try:
                response = generate_fn(case.query, case.contexts)
            except Exception as e:
                response = f"[ERROR] {e}"
            latency_ms = (time.time() - t0) * 1000
            latencies.append(latency_ms)

            results = self.metric_suite.evaluate(
                query=case.query,
                response=response,
                contexts=case.contexts,
                ground_truth=case.ground_truth,
            )

            agg = self.metric_suite.aggregate_score(results)
            passed = agg >= self.pass_threshold

            case_results.append(CaseResult(
                case_id=case.case_id,
                query=case.query,
                response=response,
                latency_ms=latency_ms,
                metrics={k: v.to_dict() for k, v in results.items()},
                aggregate_score=agg,
                passed=passed,
            ))

            for name, mr in results.items():
                metric_sums[name] = metric_sums.get(name, 0) + mr.score
                metric_counts[name] = metric_counts.get(name, 0) + 1

        duration = time.time() - start
        n = len(case_results) or 1
        passed_n = sum(1 for c in case_results if c.passed)

        return BenchmarkResult(
            benchmark_id=f"bench_{uuid.uuid4().hex[:10]}",
            name=self.name,
            total_cases=len(case_results),
            passed_cases=passed_n,
            failed_cases=len(case_results) - passed_n,
            pass_rate=passed_n / n,
            avg_score=sum(c.aggregate_score for c in case_results) / n,
            avg_latency_ms=sum(latencies) / n,
            p50_latency_ms=_percentile(latencies, 50),
            p95_latency_ms=_percentile(latencies, 95),
            p99_latency_ms=_percentile(latencies, 99),
            metric_averages={k: metric_sums[k] / metric_counts[k]
                             for k in metric_sums},
            case_results=case_results,
            duration_s=duration,
        )


def _percentile(data: Sequence[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] * (c - k) + s[c] * (k - f)


# --------------------------------- A/B Test ---------------------------------

@dataclass
class ABTestResult:
    test_id: str
    name: str
    variant_a: BenchmarkResult
    variant_b: BenchmarkResult
    winner: str               # "A" / "B" / "tie"
    metric_deltas: Dict[str, Dict[str, float]]   # {metric: {a, b, delta, delta_pct}}
    significance: Dict[str, Any]                  # 简单 t-stat
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "variant_a": self.variant_a.summary(),
            "variant_b": self.variant_b.summary(),
            "winner": self.winner,
            "metric_deltas": self.metric_deltas,
            "significance": self.significance,
            "recommendation": self.recommendation,
        }


class ABTest:
    """A/B 测试：在同一基准上对比两个生成函数。"""

    def __init__(self, name: str, benchmark: Benchmark,
                 variant_a_fn: GenerateFn, variant_b_fn: GenerateFn,
                 a_label: str = "A", b_label: str = "B"):
        self.name = name
        self.benchmark = benchmark
        self.a_fn = variant_a_fn
        self.b_fn = variant_b_fn
        self.a_label = a_label
        self.b_label = b_label

    def run(self) -> ABTestResult:
        a_result = self.benchmark.run(self.a_fn)
        b_result = self.benchmark.run(self.b_fn)

        # 各指标差异
        deltas: Dict[str, Dict[str, float]] = {}
        for metric in set(a_result.metric_averages) | set(b_result.metric_averages):
            a_val = a_result.metric_averages.get(metric, 0)
            b_val = b_result.metric_averages.get(metric, 0)
            delta = b_val - a_val
            delta_pct = (delta / a_val * 100) if a_val else 0
            deltas[metric] = {"a": round(a_val, 4), "b": round(b_val, 4),
                              "delta": round(delta, 4),
                              "delta_pct": round(delta_pct, 2)}

        # 简单 paired t-test 判断综合分显著性
        a_scores = [c.aggregate_score for c in a_result.case_results]
        b_scores = [c.aggregate_score for c in b_result.case_results]
        sig = _paired_ttest(a_scores, b_scores)

        # 决定 winner
        if abs(b_result.avg_score - a_result.avg_score) < 0.01:
            winner = "tie"
        elif b_result.avg_score > a_result.avg_score:
            winner = self.b_label
        else:
            winner = self.a_label

        if sig.get("significant"):
            recommendation = (f"Variant {winner} wins with statistical significance "
                              f"(p≈{sig['p_value']:.4f}). Recommend rollout.")
        else:
            recommendation = (f"Variant {winner} leads numerically but difference is not "
                              f"statistically significant. Continue testing or expand sample.")

        return ABTestResult(
            test_id=f"ab_{uuid.uuid4().hex[:10]}",
            name=self.name,
            variant_a=a_result,
            variant_b=b_result,
            winner=winner,
            metric_deltas=deltas,
            significance=sig,
            recommendation=recommendation,
        )


def _paired_ttest(a: Sequence[float], b: Sequence[float],
                  alpha: float = 0.05) -> Dict[str, Any]:
    """简化的 paired t-test 实现（无 scipy 依赖）。"""
    n = min(len(a), len(b))
    if n < 2:
        return {"n": n, "significant": False, "p_value": 1.0,
                "reason": "insufficient samples"}
    diffs = [a[i] - b[i] for i in range(n)]
    mean_d = statistics.mean(diffs)
    if all(d == diffs[0] for d in diffs):
        return {"n": n, "mean_diff": mean_d, "significant": False,
                "p_value": 1.0, "t_stat": 0.0}
    sd = statistics.stdev(diffs)
    se = sd / math.sqrt(n)
    t_stat = mean_d / se if se else 0
    # 双尾 p 近似（df=n-1，使用正态近似）
    p_value = 2 * (1 - _normal_cdf(abs(t_stat)))
    return {
        "n": n,
        "mean_diff": round(mean_d, 4),
        "std_diff": round(sd, 4),
        "t_stat": round(t_stat, 4),
        "p_value": round(p_value, 4),
        "significant": p_value < alpha,
    }


def _normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
