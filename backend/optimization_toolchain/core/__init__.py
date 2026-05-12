"""
优化工具链 - 核心组件
包含基类、注册表、任务队列、基准测试框架
"""
from .base import (
    BaseOptimizer,
    OptimizationConfig,
    OptimizationResult,
    PerformanceMetrics,
    OptimizationType,
    QuantizationMethod,
    DistillationMode,
    DistillationLossType,
)
from .registry import OptimizationRegistry
from .task_queue import TaskQueue, OptimizationTask, TaskStatus
from .benchmark import (
    BenchmarkSuite,
    BenchmarkConfig,
    BenchmarkResult,
    compare_results,
    print_comparison,
)

__all__ = [
    # 基类
    "BaseOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "PerformanceMetrics",
    "OptimizationType",
    "QuantizationMethod",
    "DistillationMode",
    "DistillationLossType",
    
    # 注册表
    "OptimizationRegistry",
    
    # 任务队列
    "TaskQueue",
    "OptimizationTask",
    "TaskStatus",
    
    # 基准测试
    "BenchmarkSuite",
    "BenchmarkConfig",
    "BenchmarkResult",
    "compare_results",
    "print_comparison",
]
