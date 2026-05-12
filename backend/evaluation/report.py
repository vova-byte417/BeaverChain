"""质量报告生成器：把 BenchmarkResult / ABTestResult / GuardrailEngine.audit 渲染成报告."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .benchmark import BenchmarkResult, ABTestResult
from .guardrails import AuditLog


class ReportFormat(Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


@dataclass
class QualityReport:
    title: str
    benchmarks: List[BenchmarkResult] = None  # type: ignore
    ab_tests: List[ABTestResult] = None       # type: ignore
    audit_log: Optional[AuditLog] = None
    metadata: Dict[str, Any] = None           # type: ignore

    def __post_init__(self):
        if self.benchmarks is None:
            self.benchmarks = []
        if self.ab_tests is None:
            self.ab_tests = []
        if self.metadata is None:
            self.metadata = {}

    # -------------------- 渲染 --------------------

    def render(self, fmt: ReportFormat = ReportFormat.MARKDOWN) -> str:
        if fmt == ReportFormat.JSON:
            return self.to_json()
        if fmt == ReportFormat.MARKDOWN:
            return self.to_markdown()
        if fmt == ReportFormat.HTML:
            return self.to_html()
        raise ValueError(f"Unsupported format: {fmt}")

    def save(self, path: str, fmt: Optional[ReportFormat] = None) -> None:
        if fmt is None:
            if path.endswith(".json"):
                fmt = ReportFormat.JSON
            elif path.endswith(".html"):
                fmt = ReportFormat.HTML
            else:
                fmt = ReportFormat.MARKDOWN
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.render(fmt))

    # -------------------- JSON --------------------

    def to_json(self) -> str:
        data = {
            "title": self.title,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": self.metadata,
            "benchmarks": [b.to_dict() for b in self.benchmarks],
            "ab_tests": [t.to_dict() for t in self.ab_tests],
            "audit_stats": self.audit_log.stats() if self.audit_log else None,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    # -------------------- Markdown --------------------

    def to_markdown(self) -> str:
        lines: List[str] = [
            f"# {self.title}",
            "",
            f"_Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}_",
            "",
        ]

        if self.metadata:
            lines.append("## Metadata")
            for k, v in self.metadata.items():
                lines.append(f"- **{k}**: {v}")
            lines.append("")

        # Benchmark
        if self.benchmarks:
            lines.append("## Benchmark Results")
            lines.append("")
            for b in self.benchmarks:
                lines.append(f"### {b.name} (`{b.benchmark_id}`)")
                lines.append("")
                lines.append("| Metric | Value |")
                lines.append("| --- | --- |")
                lines.append(f"| Total cases | {b.total_cases} |")
                lines.append(f"| Pass rate | {b.pass_rate:.2%} |")
                lines.append(f"| Avg score | {b.avg_score:.4f} |")
                lines.append(f"| Avg latency | {b.avg_latency_ms:.1f} ms |")
                lines.append(f"| P50 latency | {b.p50_latency_ms:.1f} ms |")
                lines.append(f"| P95 latency | {b.p95_latency_ms:.1f} ms |")
                lines.append(f"| P99 latency | {b.p99_latency_ms:.1f} ms |")
                lines.append(f"| Duration | {b.duration_s:.2f} s |")
                lines.append("")

                if b.metric_averages:
                    lines.append("**Per-metric averages:**")
                    lines.append("")
                    lines.append("| Metric | Score |")
                    lines.append("| --- | --- |")
                    for k, v in sorted(b.metric_averages.items()):
                        lines.append(f"| {k} | {v:.4f} |")
                    lines.append("")

                # 失败 case 简表
                failed = [c for c in b.case_results if not c.passed]
                if failed:
                    lines.append(f"**Failed cases ({len(failed)}):**")
                    lines.append("")
                    lines.append("| Case ID | Score | Query |")
                    lines.append("| --- | --- | --- |")
                    for c in failed[:10]:
                        q = c.query[:60].replace("|", "\\|")
                        lines.append(f"| `{c.case_id}` | {c.aggregate_score:.3f} | {q} |")
                    if len(failed) > 10:
                        lines.append(f"| ... | ... | (+{len(failed)-10} more) |")
                    lines.append("")

        # A/B Test
        if self.ab_tests:
            lines.append("## A/B Tests")
            lines.append("")
            for t in self.ab_tests:
                lines.append(f"### {t.name} (`{t.test_id}`)")
                lines.append("")
                lines.append(f"**Winner:** {t.winner}")
                lines.append("")
                lines.append(f"**Recommendation:** {t.recommendation}")
                lines.append("")
                lines.append("| Metric | Variant A | Variant B | Δ | Δ% |")
                lines.append("| --- | --- | --- | --- | --- |")
                for metric, d in sorted(t.metric_deltas.items()):
                    arrow = "↑" if d["delta"] > 0 else ("↓" if d["delta"] < 0 else "=")
                    lines.append(f"| {metric} | {d['a']:.4f} | {d['b']:.4f} | "
                                 f"{arrow}{abs(d['delta']):.4f} | {d['delta_pct']:+.2f}% |")
                lines.append("")
                if t.significance:
                    sig = t.significance
                    lines.append(f"**Significance:** n={sig.get('n')}, "
                                 f"p={sig.get('p_value', 1):.4f}, "
                                 f"significant={sig.get('significant', False)}")
                    lines.append("")

        # Guardrails
        if self.audit_log:
            stats = self.audit_log.stats()
            lines.append("## Guardrails Audit Summary")
            lines.append("")
            lines.append(f"- **Total violations:** {stats['total']}")
            if stats["by_severity"]:
                lines.append("")
                lines.append("**By severity:**")
                lines.append("")
                lines.append("| Severity | Count |")
                lines.append("| --- | --- |")
                for sev, n in sorted(stats["by_severity"].items()):
                    lines.append(f"| {sev} | {n} |")
                lines.append("")
            if stats["by_rule"]:
                lines.append("**By rule:**")
                lines.append("")
                lines.append("| Rule | Hits |")
                lines.append("| --- | --- |")
                for rule, n in sorted(stats["by_rule"].items(),
                                       key=lambda x: -x[1])[:20]:
                    lines.append(f"| {rule} | {n} |")
                lines.append("")

        # 总结
        lines.append("## Summary")
        lines.append("")
        if self.benchmarks:
            best = max(self.benchmarks, key=lambda b: b.avg_score)
            lines.append(f"- Best benchmark: **{best.name}** (avg_score={best.avg_score:.4f})")
        if self.ab_tests:
            decisive = [t for t in self.ab_tests
                         if t.significance.get("significant")]
            lines.append(f"- A/B tests with significant result: {len(decisive)} / "
                         f"{len(self.ab_tests)}")
        if self.audit_log:
            stats = self.audit_log.stats()
            critical = stats["by_severity"].get("critical", 0)
            high = stats["by_severity"].get("high", 0)
            if critical or high:
                lines.append(f"- ⚠️ {critical} critical / {high} high-severity guardrail "
                             f"violations require attention")

        return "\n".join(lines)

    # -------------------- HTML --------------------

    def to_html(self) -> str:
        # 简单：把 markdown 包成 html
        md = self.to_markdown()
        # 极简渲染（避免外部依赖）
        body = md.replace("\n", "<br>\n")
        return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>{self.title}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 960px; margin: 2em auto; padding: 0 1em; color: #333; }}
  table {{ border-collapse: collapse; margin: 1em 0; }}
  td, th {{ border: 1px solid #ddd; padding: 6px 12px; }}
  th {{ background: #f6f8fa; }}
  code {{ background: #f6f8fa; padding: 2px 6px; border-radius: 3px; }}
  h1 {{ border-bottom: 2px solid #333; }}
  h2 {{ border-bottom: 1px solid #ccc; margin-top: 2em; }}
</style>
</head><body>
<pre style="white-space: pre-wrap; font-family: inherit;">{md}</pre>
</body></html>"""
