"""
优化工具链 - 基类定义
定义所有优化器的通用接口和数据结构
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class OptimizationType(str, Enum):
    """优化类型枚举"""
    QUANTIZATION = "quantization"      # 量化
    DISTILLATION = "distillation"      # 知识蒸馏
    PRUNING = "pruning"                # 剪枝
    INFERENCE = "inference"            # 推理优化
    COMPRESSION = "compression"        # 模型压缩


class QuantizationMethod(str, Enum):
    """量化方法枚举"""
    GPTQ = "gptq"                      # GPTQ 量化
    AWQ = "awq"                        # AWQ 量化
    SQUEEZELLM = "squeezellm"          # SqueezeLLM 量化
    INT8 = "int8"                      # 8-bit 量化
    INT4 = "int4"                      # 4-bit 量化
    FP8 = "fp8"                        # FP8 量化


class DistillationMode(str, Enum):
    """蒸馏模式枚举"""
    STANDARD = "standard"               # 标准蒸馏
    LIGHTWEIGHT = "lightweight"         # 轻量级蒸馏
    SELF_DISTILL = "self_distill"       # 自蒸馏
    ONLINE = "online"                   # 在线蒸馏


@dataclass
class OptimizationConfig:
    """优化配置基类"""
    name: str
    description: Optional[str] = None
    optimization_type: OptimizationType = OptimizationType.QUANTIZATION
    
    # 通用配置
    model_name_or_path: str = ""
    output_dir: str = "./output"
    device: str = "cuda"
    dtype: str = "float16"
    
    # 保存配置
    save_checkpoint: bool = True
    save_format: str = "safetensors"
    
    # 附加参数
    extra_args: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


@dataclass
class PerformanceMetrics:
    """性能指标"""
    # 速度指标
    latency_avg: float = 0.0           # 平均延迟 (ms)
    latency_p50: float = 0.0           # P50 延迟
    latency_p95: float = 0.0           # P95 延迟
    latency_p99: float = 0.0           # P99 延迟
    throughput: float = 0.0            # 吞吐量 (tokens/s)
    
    # 内存指标
    memory_usage: float = 0.0           # 内存使用 (MB)
    memory_peak: float = 0.0            # 内存峰值 (MB)
    gpu_memory_usage: float = 0.0       # GPU 内存使用 (MB)
    
    # 质量指标
    perplexity: Optional[float] = None  # 困惑度
    accuracy: Optional[float] = None     # 准确率
    bleu_score: Optional[float] = None   # BLEU 分数
    rouge_score: Optional[Dict[str, float]] = None  # ROUGE 分数
    
    # 模型大小
    model_size_original: float = 0.0    # 原始模型大小 (MB)
    model_size_optimized: float = 0.0   # 优化后模型大小 (MB)
    compression_ratio: float = 0.0       # 压缩率


@dataclass
class OptimizationResult:
    """优化结果"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    success: bool = False
    
    # 配置信息
    config: Optional[OptimizationConfig] = None
    optimization_type: Optional[OptimizationType] = None
    
    # 输出信息
    output_path: Optional[str] = None
    checkpoint_path: Optional[str] = None
    
    # 性能指标
    metrics_before: Optional[PerformanceMetrics] = None
    metrics_after: Optional[PerformanceMetrics] = None
    
    # 时间信息
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # 日志和错误
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    # 附加信息
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_log(self, message: str) -> None:
        """添加日志"""
        timestamp = datetime.now().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
    
    def calculate_improvements(self) -> Dict[str, float]:
        """计算性能改进百分比"""
        if not self.metrics_before or not self.metrics_after:
            return {}
        
        improvements = {}
        
        # 延迟改进 (越小越好)
        if self.metrics_before.latency_avg > 0:
            improvements["latency_improvement"] = (
                (self.metrics_before.latency_avg - self.metrics_after.latency_avg)
                / self.metrics_before.latency_avg * 100
            )
        
        # 吞吐量改进 (越大越好)
        if self.metrics_before.throughput > 0:
            improvements["throughput_improvement"] = (
                (self.metrics_after.throughput - self.metrics_before.throughput)
                / self.metrics_before.throughput * 100
            )
        
        # 内存节省
        if self.metrics_before.gpu_memory_usage > 0:
            improvements["memory_saving"] = (
                (self.metrics_before.gpu_memory_usage - self.metrics_after.gpu_memory_usage)
                / self.metrics_before.gpu_memory_usage * 100
            )
        
        # 模型压缩率
        if self.metrics_before.model_size_original > 0:
            improvements["compression_ratio"] = (
                self.metrics_before.model_size_original
                / self.metrics_after.model_size_optimized
            )
        
        return improvements
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "optimization_type": self.optimization_type.value if self.optimization_type else None,
            "output_path": self.output_path,
            "duration_seconds": self.duration_seconds,
            "metrics_before": self.metrics_before.__dict__ if self.metrics_before else None,
            "metrics_after": self.metrics_after.__dict__ if self.metrics_after else None,
            "improvements": self.calculate_improvements(),
            "error_message": self.error_message,
            "logs": self.logs[-50:] if len(self.logs) > 50 else self.logs,  # 只保留最近 50 条
            "metadata": self.metadata,
        }


class BaseOptimizer(ABC):
    """优化器基类"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self._result = OptimizationResult(
            config=config,
            optimization_type=config.optimization_type
        )
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否合法
        
        Returns:
            bool: 配置是否有效
        """
        pass
    
    @abstractmethod
    def benchmark_before(self) -> PerformanceMetrics:
        """
        优化前基准测试
        
        Returns:
            PerformanceMetrics: 优化前性能指标
        """
        pass
    
    @abstractmethod
    def optimize(self) -> bool:
        """
        执行优化
        
        Returns:
            bool: 优化是否成功
        """
        pass
    
    @abstractmethod
    def benchmark_after(self) -> PerformanceMetrics:
        """
        优化后基准测试
        
        Returns:
            PerformanceMetrics: 优化后性能指标
        """
        pass
    
    @abstractmethod
    def save_result(self) -> str:
        """
        保存优化结果
        
        Returns:
            str: 输出路径
        """
        pass
    
    def run(self) -> OptimizationResult:
        """
        执行完整的优化流程
        
        Returns:
            OptimizationResult: 优化结果
        """
        self._result.started_at = datetime.now()
        self._result.add_log(f"开始 {self.config.optimization_type.value} 优化")
        
        try:
            # 1. 验证配置
            self._result.add_log("步骤 1/4: 验证配置")
            if not self.validate_config():
                raise ValueError("配置验证失败")
            
            # 2. 优化前基准测试
            self._result.add_log("步骤 2/4: 执行优化前基准测试")
            self._result.metrics_before = self.benchmark_before()
            
            # 3. 执行优化
            self._result.add_log("步骤 3/4: 执行优化")
            if not self.optimize():
                raise RuntimeError("优化执行失败")
            
            # 4. 优化后基准测试
            self._result.add_log("步骤 4/4: 执行优化后基准测试")
            self._result.metrics_after = self.benchmark_after()
            
            # 保存结果
            self._result.add_log("保存优化结果")
            self._result.output_path = self.save_result()
            
            self._result.success = True
            self._result.add_log("优化完成")
            
        except Exception as e:
            self._result.success = False
            self._result.error_message = str(e)
            self._result.add_log(f"优化失败: {str(e)}")
        
        finally:
            self._result.completed_at = datetime.now()
            if self._result.started_at:
                self._result.duration_seconds = (
                    self._result.completed_at - self._result.started_at
                ).total_seconds()
        
        return self._result
