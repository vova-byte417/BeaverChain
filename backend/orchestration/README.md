# Orchestration & Lineage Module

> Task 5: 多模型/多 Agent 编排引擎 + 完整的调用链 (Lineage) 追踪系统

## 概述

`orchestration/` 提供两大能力：

1. **多模型/多 Agent 编排** - 用 DAG 描述多步骤工作流，支持条件分支、并行执行、循环迭代、Agent 协作。
2. **Lineage 追踪** - OpenTelemetry 风格的 Span 树，记录每个节点的输入/输出/耗时/Token/工具调用，支持持久化、查询、可视化。

## 模块结构

```
orchestration/
├── __init__.py              # 包入口
├── core/                    # 编排引擎核心
│   ├── workflow.py          # Workflow / Node / Edge 数据结构
│   ├── executor.py          # 异步执行器 + 并行执行
│   └── conditions.py        # 条件 + 循环 DSL
├── lineage/                 # Lineage 追踪
│   ├── tracker.py           # LineageTracker / Span / Record / Graph
│   ├── storage.py           # 内存 / 文件 / 混合存储
│   └── query.py             # 查询构建器
├── models.py                # Agent / ToolCall / Snapshot 数据模型
├── visualization.py         # Mermaid / Graphviz / Gantt 渲染
├── dsl.py                   # JSON/YAML/dict DSL 解析
├── api.py                   # FastAPI 路由（可视化 API）
└── examples.py              # 4 个端到端示例
```

## 快速开始

### 1. 编程方式定义工作流

```python
import asyncio
from orchestration import (
    Workflow, WorkflowNode, WorkflowEdge, NodeType,
    WorkflowExecutor, LineageTracker,
)

wf = Workflow(name="qa_pipeline")
wf.add_nodes([
    WorkflowNode.create("Retrieve", NodeType.TOOL, node_id="r",
                        config={"tool_name": "vector_search"}),
    WorkflowNode.create("Generate", NodeType.MODEL, node_id="g",
                        config={"model_name": "gpt-4"}),
])
wf.connect("r", "g").set_entry_point("r").add_exit_point("g")

tracker = LineageTracker()
executor = WorkflowExecutor(wf, lineage_tracker=tracker)
result = asyncio.run(executor.execute({"query": "What is RAG?"}))
print(result.status, result.duration)
```

### 2. DSL 方式定义

```python
from orchestration import WorkflowDSL

spec = {
    "name": "router",
    "nodes": [
        {"id": "cls", "name": "Classify", "type": "model"},
        {"id": "a", "name": "Code agent", "type": "agent"},
        {"id": "b", "name": "Search agent", "type": "agent"},
    ],
    "edges": [
        {"from": "cls", "to": "a",
         "condition": {"op": "equals", "key": "intent", "value": "code"},
         "label": "intent=code"},
        {"from": "cls", "to": "b",
         "condition": {"op": "equals", "key": "intent", "value": "search"},
         "label": "intent=search"},
    ],
    "entry": "cls",
}
wf = WorkflowDSL.from_dict(spec)
```

### 3. 查询 Lineage

```python
from orchestration.lineage import LineageQuery, FileStorage

storage = FileStorage("./lineage_data")
records = (
    LineageQuery(storage)
    .filter_workflow_name("qa_pipeline")
    .filter_success(True)
    .filter_last(hours=24)
    .filter_min_duration(100)
    .sort_by("duration_ms", descending=True)
    .limit(10)
    .execute()
)
stats = LineageQuery(storage).filter_last(24).aggregate()
print(stats)  # count, avg_duration_ms, total_tokens, success_rate, ...
```

### 4. 可视化

```python
from orchestration.visualization import Visualizer, GraphFormat, TimelineVisualizer

# Workflow 结构图
print(Visualizer.render(wf, GraphFormat.MERMAID))

# Lineage 调用链
record = tracker.get_record(result.run_id)
print(Visualizer.render(record, GraphFormat.MERMAID))

# 执行时间线
print(TimelineVisualizer.to_text_timeline(record))
print(TimelineVisualizer.to_mermaid_gantt(record))
```

## 核心特性

### 编排
| 特性 | 说明 |
|------|------|
| **节点类型** | start, end, model, agent, tool, condition, parallel, loop, aggregate |
| **条件分支** | equals, gt/lt, contains, matches, and/or, custom function |
| **并行执行** | DAG 自动识别可并行节点 + `ParallelExecutor` 多工作流并发 |
| **循环** | `LoopSpec.for_range / for_each / while_` |
| **重试** | 节点级 `retry_config`，支持指数退避 |
| **超时** | 节点级 `timeout` 字段 |
| **输入输出映射** | `input_mapping` / `output_mapping` 实现节点解耦 |
| **校验** | `Workflow.validate()`：DAG 检查 + 孤立节点检查 + 边引用检查 |

### Lineage
| 特性 | 说明 |
|------|------|
| **Span 树** | OpenTelemetry 风格，workflow → node → tool 三层嵌套 |
| **输入输出快照** | `record_node_inputs/outputs`，自动脱敏 (password/secret/token/key) |
| **Token 统计** | `record_token_usage` 累积 prompt/completion/total |
| **延迟统计** | 自动计算 `duration_ms`、关键路径、瓶颈节点 |
| **工具调用记录** | `record_tool_call` 单独 Span，含参数/结果 |
| **Agent 信息** | `record_agent_info` 记录 role + config |
| **存储后端** | `InMemoryStorage` / `FileStorage` / `HybridStorage`（带索引） |
| **查询** | 流式 API：`filter_*().sort_by().limit().execute()` 或 `.aggregate()` / `.group_by()` |
| **导入导出** | `tracker.export_record(run_id, path)` / `tracker.import_record(path)` |

### 可视化
| 输出 | 说明 |
|------|------|
| **Mermaid graph TD** | Workflow 结构图 + Lineage Span 树（带样式） |
| **Graphviz DOT** | 适合复杂 DAG 渲染 |
| **Mermaid Gantt** | 执行时间线，按 span_type 分组 |
| **文本时间线** | 控制台友好，缩进显示父子关系 |
| **关键路径分析** | `LineageGraph.get_critical_path()` |
| **瓶颈识别** | `LineageGraph.get_bottlenecks(threshold_ms)` |

### REST API（可选）
`api.py` 暴露 FastAPI router，可挂到主服务：

```python
from fastapi import FastAPI
from orchestration.api import router

app = FastAPI()
app.include_router(router)
# POST /orchestration/workflows/run
# POST /orchestration/workflows/validate
# GET  /orchestration/workflows/render
# GET  /orchestration/lineage/{run_id}
# GET  /orchestration/lineage/{run_id}/graph
# GET  /orchestration/lineage/{run_id}/timeline
# GET  /orchestration/lineage?last_hours=24&success=true
# GET  /orchestration/lineage/stats/aggregate
```

## 与系统其他模块的集成

- **Model Registry (task-3)** - `model` / `agent` 节点的 `config.model_name` 直接对应 Registry 中的版本号；执行前可调 Registry API 解析具体权重路径。
- **Optimization Toolchain (task-4)** - `tool` 节点可包装 vLLM/TGI 引擎实例，量化/蒸馏后的模型透明替换。
- **Architecture (task-2)** - 与 ARCHITECTURE.md 中的 Orchestration Layer 对齐：DAG 执行 + 全链路追踪 + 多 Agent 协作三层职责。

## 端到端示例

`orchestration/examples.py` 提供 4 个示例：

1. `build_simple_qa_workflow()` - 线性 RAG 流水线
2. `build_router_workflow()` - 基于 intent 的条件路由
3. `build_multi_agent_workflow()` - planner + 3 并行 executor + reviewer
4. `DSL_EXAMPLE` - DSL 定义的完整 RAG 流程

运行：

```bash
python -m orchestration.examples
```

## 验证

已通过的检查：
- `import orchestration` 成功，导出 23 个公共符号
- `examples.run_example(build_simple_qa_workflow(), {...})` 端到端运行成功
- Mermaid / 文本时间线 / Lineage Span 树 输出正确
- Token 统计、Span 父子关系、状态正确传播

## 版本

- **v1.0.0** - 初始版本，覆盖编排 + Lineage + 可视化 + DSL + API
