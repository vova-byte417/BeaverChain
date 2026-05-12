# Evaluation & Quality Assurance Module

> Task 6: 评估与质量保障模块 — 解决大模型输出非确定性

## 概述

`evaluation/` 把"如何衡量大模型质量"和"如何兜住质量底线"封装成 5 个解耦子模块：

| 子模块 | 职责 |
|------|------|
| `metrics` | 6 个核心指标的启发式实现 + LLM-as-judge 接口 |
| `guardrails` | 输入/输出规则引擎 + 审计日志 |
| `rag_quality` | 检索质量（P/R/F1/MRR/nDCG）+ 上下文利用率 |
| `benchmark` | 基准测试运行器 + A/B 测试 + 简化 paired t-test |
| `report` | 质量报告生成器（JSON / Markdown / HTML） |

设计原则：**零外部依赖即可跑通**（启发式实现），生产中通过 `judge_fn` 注入真实 LLM-as-judge 即可升级。

## 模块结构

```
evaluation/
├── __init__.py
├── metrics.py        # 6 metrics + MetricSuite
├── guardrails.py     # 规则引擎 + AuditLog
├── rag_quality.py    # 检索评估 + 上下文利用率
├── benchmark.py      # Benchmark + ABTest
├── report.py         # QualityReport（多格式输出）
├── examples.py       # 端到端示例
└── README.md
```

## 核心能力速览

### 1. Metrics — 一行评估

```python
from evaluation import MetricSuite

suite = MetricSuite()
results = suite.evaluate(
    query="What is the capital of France?",
    response="Paris is the capital of France.",
    context="Paris is the capital and most populous city of France.",
    ground_truth="Paris",
)
# {'hallucination': MetricResult(score=1.0, ...), 'toxicity': ..., 'faithfulness': ..., ...}
```

| 指标 | 含义 | higher_is_better |
|------|------|---|
| `hallucination` | 句子级与 context 不重叠的占比 | ❌ |
| `toxicity` | 词典 + 模式命中比例 | ❌ |
| `faithfulness` | response bigram 被 context 支持的比例 | ✅ |
| `relevance` | response 与 query 的覆盖 + bigram 重叠 | ✅ |
| `context_recall` | ground_truth token 被 context 覆盖率 | ✅ |
| `context_precision` | context 中相关比例 | ✅ |

每个 metric 都支持 `judge_fn=callable(prompt, response)->float`，注入后启发式自动让位给真实 judge。

### 2. Guardrails — 安全护栏

```python
from evaluation import GuardrailEngine, GuardrailRule, RuleAction, AuditLog

audit = AuditLog(file_path="audit.jsonl")
engine = GuardrailEngine.default(audit_log=audit)
# 默认规则：prompt-injection / PII / 输出长度 / 毒性词

decision = engine.evaluate(user_input, direction="input")
if not decision.allowed:
    return f"Blocked by {decision.blocked_by}"

decision = engine.evaluate(model_output, direction="output")
final_text = decision.content   # 已 redact 邮箱/手机/身份证/卡号
```

**规则类型**: `regex / keyword / pii / prompt_injection / length_max / length_min / custom`
**动作**: `block / redact / warn / rewrite / log_only`
**严重度**: `low / medium / high / critical`，全部进 `AuditLog` 可按维度统计。

### 3. RAG Quality — 一站式 RAG 监控

```python
from evaluation import RAGQualityMonitor

monitor = RAGQualityMonitor(ndcg_k=5)
report = monitor.full_evaluate(
    query=...,
    response=...,
    contexts=[...],            # 检索回的 K 个文档
    ground_truth=...,
    relevant_doc_ids=[0, 2],   # 可选：标注的相关 ID
)
# composite_score + retrieval(P/R/F1/MRR/nDCG/hit_rate) + context_utilization + faithfulness + relevance
```

`evaluate_context_utilization` 单独可调，告诉你 LLM 实际用了几条 context、哪些被浪费。

### 4. Benchmark + A/B 测试

```python
from evaluation import Benchmark, ABTest

bench = Benchmark.standard_qa()  # 内置 3 个 case，或 from_jsonl(name, path)
result = bench.run(my_model_fn)
# pass_rate / avg_score / p50/p95/p99 latency / per-metric averages

ab = ABTest("v1_vs_v2", bench, model_a_fn, model_b_fn,
            a_label="GPT-baseline", b_label="GPT-experimental")
ab_result = ab.run()
# winner / metric_deltas / paired t-test significance / recommendation
```

A/B 测试内置简化的 paired t-test（无 scipy 依赖），返回 p-value 和"是否显著"。

### 5. Quality Report

```python
from evaluation import QualityReport, ReportFormat

report = QualityReport(
    title="Weekly QA Report",
    benchmarks=[result_a, result_b],
    ab_tests=[ab_result],
    audit_log=engine.audit_log,
    metadata={"week": "2026-W19"},
)
report.save("qa_report.md")           # Markdown
report.save("qa_report.json")         # JSON
report.save("qa_report.html")         # HTML
```

报告自动汇总：每个基准的 pass_rate / latency / per-metric 平均；A/B 的 winner/delta/significance；guardrails 按严重度/规则的命中分布；尾部给出 critical/high 警示。

## 与系统其他模块的集成

| 来源模块 | 集成点 |
|------|------|
| `model_registry` (task-3) | A/B 两个 variant 直接对应 Registry 的两个版本 |
| `optimization_toolchain` (task-4) | benchmark 可对比量化前后、不同推理引擎的质量+延迟 |
| `orchestration` (task-5) | guardrails 作为 input/output 节点的拦截器；metrics 写入 LineageRecord 的 metadata |
| `architecture` (task-2) | Guardrails Layer + Quality Layer 的具体落地 |

## 验证

已通过的检查（`python -m evaluation.examples`）：

- ✓ MetricSuite 6 项指标全部有非空输出
- ✓ Guardrails 拦截 prompt injection（critical），脱敏邮箱+手机号
- ✓ AuditLog 按 severity / rule 正确聚合
- ✓ RAGQualityMonitor 综合分计算正确（composite=0.79，retrieval F1=1.0）
- ✓ Benchmark.standard_qa() 三个 case 全 pass，pass_rate=100%
- ✓ ABTest 输出 winner / 显著性 / 推荐
- ✓ QualityReport markdown/json/html 三种格式渲染正常

## 升级路径

| 启发式实现 | 生产升级 |
|------|------|
| Toxicity 词典 | Detoxify / Perspective API（赋值给 `judge_fn`） |
| Hallucination 句级重叠 | RAGAS / TruLens / GPT-4 judge |
| Significance test 正态近似 | scipy.stats.ttest_rel 或 bootstrap |
| AuditLog jsonl 文件 | OpenTelemetry / Sentry / 数据库后端 |

所有升级都不需要改业务代码 — 通过依赖注入即可。
