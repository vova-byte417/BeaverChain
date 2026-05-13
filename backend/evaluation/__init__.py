"""Evaluation & Quality Assurance Module.

提供：
- metrics: hallucination / toxicity / faithfulness / relevance / context recall&precision
- guardrails: 输入/输出过滤规则引擎 + 审计日志
- rag_quality: RAG 检索质量与上下文利用率监控
- benchmark: 标准数据集 + A/B 测试 + 性能对比报告
- report: 质量报告生成器
"""

__version__ = "1.0.0"

from .metrics import (
    MetricResult,
    HallucinationMetric,
    ToxicityMetric,
    FaithfulnessMetric,
    RelevanceMetric,
    ContextRecallMetric,
    ContextPrecisionMetric,
    MetricSuite,
)
from .guardrails import (
    GuardrailRule,
    RuleType,
    RuleAction,
    GuardrailEngine,
    AuditLog,
    GuardrailViolation,
)
from .rag_quality import (
    RAGQualityMonitor,
    RetrievalEvalResult,
    ContextUtilization,
)
from .benchmark import (
    Benchmark,
    BenchmarkCase,
    BenchmarkResult,
    ABTest,
    ABTestResult,
)
from .report import QualityReport, ReportFormat

__all__ = [
    # metrics
    "MetricResult", "HallucinationMetric", "ToxicityMetric",
    "FaithfulnessMetric", "RelevanceMetric",
    "ContextRecallMetric", "ContextPrecisionMetric", "MetricSuite",
    # guardrails
    "GuardrailRule", "RuleType", "RuleAction",
    "GuardrailEngine", "AuditLog", "GuardrailViolation",
    # rag
    "RAGQualityMonitor", "RetrievalEvalResult", "ContextUtilization",
    # benchmark
    "Benchmark", "BenchmarkCase", "BenchmarkResult", "ABTest", "ABTestResult",
    # report
    "QualityReport", "ReportFormat",
]
