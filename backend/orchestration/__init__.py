"""
多模型编排与 Lineage 追踪模块
Multi-Model Orchestration & Lineage Tracking Module
"""

__version__ = "1.0.0"
__author__ = "BeaverChain Team"

# 核心组件
from .core import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowExecutor,
    ExecutionStatus,
    NodeType,
)

# Lineage 追踪
from .lineage import (
    LineageTracker,
    LineageRecord,
    LineageGraph,
    Span,
    MetricType,
)

# 数据模型
from .models import (
    Agent,
    AgentRole,
    ToolCall,
    ExecutionSnapshot,
    TokenStats,
    LatencyStats,
)

# 可视化
from .visualization import (
    Visualizer,
    GraphFormat,
    TimelineVisualizer,
)

# DSL 解析器
from .dsl import (
    WorkflowDSL,
    DSLError,
    dsl_parser,
)

__all__ = [
    # 核心编排
    "Workflow",
    "WorkflowNode",
    "WorkflowEdge",
    "WorkflowExecutor",
    "ExecutionStatus",
    "NodeType",
    
    # Lineage 追踪
    "LineageTracker",
    "LineageRecord",
    "LineageGraph",
    "Span",
    "MetricType",
    
    # 数据模型
    "Agent",
    "AgentRole",
    "ToolCall",
    "ExecutionSnapshot",
    "TokenStats",
    "LatencyStats",
    
    # 可视化
    "Visualizer",
    "GraphFormat",
    "TimelineVisualizer",
    
    # DSL
    "WorkflowDSL",
    "DSLError",
    "dsl_parser",
]
