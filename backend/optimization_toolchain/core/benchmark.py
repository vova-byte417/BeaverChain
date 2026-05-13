"""
优化工具链 - 基准测试框架
用于统一测试优化前后的性能对比
"""
import time
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import numpy as np

from .base import PerformanceMetrics


@dataclass
class BenchmarkConfig:
    """基准测试配置"""
    name: str = "default"
    description: str = ""
    
    # 测试配置
    batch_size: int = 1
    max_new_tokens: int = 256
    num_runs: int = 10          # 运行次数
    warmup_runs: int = 2            # 预热次数
    
    # 输入配置
    prompt: str = "Hello, world!"
    prompts: List[str] = field(default_factory=list)
    
    # 数据集配置
    dataset_name: str = "default"
    dataset_size: int = 100
    
    # 度量配置
    measure_latency: bool = True
    measure_throughput: bool = True
    measure_memory: bool = True
    measure_quality: bool = False
    
    # 输出配置
    save_results: bool = True
    output_dir: str = "./benchmark_results"


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    config: BenchmarkConfig
    metrics: PerformanceMetrics
    model_name: str = ""
    model_type: str = ""
    completed_at: datetime = field(default_factory=datetime.now)
    
    # 详细统计
    latency_stats: Dict[str, float] = field(default_factory=dict)
    memory_stats: Dict[str, float] = field(default_factory=dict)
    
    # 原始数据
    raw_latencies: List[float] = field(default_factory=list)
    raw_throughputs: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "completed_at": self.completed_at.isoformat(),
            "config": asdict(self.config),
            "metrics": {
                "latency_avg": self.metrics.latency_avg,
                "latency_p50": self.metrics.latency_p50,
                "latency_p95": self.metrics.latency_p95,
                "latency_p99": self.metrics.latency_p99,
                "throughput": self.metrics.throughput,
                "memory_usage": self.metrics.memory_usage,
                "gpu_memory_usage": self.metrics.gpu_memory_usage,
            },
            "latency_stats": self.latency_stats,
            "memory_stats": self.memory_stats,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def save_to_file(self, filepath: str) -> None:
        """保存到文件"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())


class BenchmarkSuite:
    """基准测试套件"""
    
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or BenchmarkConfig()
        self._model = None
        self._tokenizer = None
    
    def load_model(self, model_name_or_path: str, model_type: str = "auto") -> None:
        """
        加载模型（预留接口）
        
        Args:
            model_name_or_path: 模型名称或路径
            model_type: 模型类型
        """
        # 这是一个模拟实现
        self.model_name = model_name_or_path
        self.model_type = model_type
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用情况（MB）"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except:
            return 0.0
    
    def _get_gpu_memory_usage(self) -> float:
        """获取 GPU 内存使用情况（MB）"""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.max_memory_allocated() / (1024 * 1024)
        except:
            pass
        return 0.0
    
    def _run_single_inference(self, prompt: str) -> tuple[float, int]:
        """
        运行单次推理
        
        Returns:
            (推理时间秒, 生成 token 数)
        """
        # 这是一个模拟实现
        start_time = time.perf_counter()
        
        # 模拟推理耗时
        time.sleep(0.05 + len(prompt) * 0.0001)
        
        elapsed = time.perf_counter() - start_time
        
        # 模拟生成的 token 数
        tokens_generated = self.config.max_new_tokens
        
        return elapsed, tokens_generated
    
    def _calculate_perplexity(self, texts: List[str]) -> float:
        """计算困惑度（模拟）"""
        # 实际实现需要真实的 perplexity 计算
        return 12.5  # 模拟值
    
    def run(self, model_name_or_path: Optional[str] = None) -> BenchmarkResult:
        """
        运行基准测试
        
        Args:
            model_name_or_path: 模型名称或路径
            
        Returns:
            基准测试结果
        """
        if model_name_or_path:
            self.load_model(model_name_or_path)
        
        model_name = getattr(self, 'model_name', model_name_or_path or 'unknown')
        model_type = getattr(self, 'model_type', 'unknown')
        
        print(f"开始基准测试: {model_name}")
        
        # 1. 预热
        print(f"  预热阶段 ({self.config.warmup_runs} 次)...")
        warmup_prompt = self.config.prompts[0] if self.config.prompts else self.config.prompt
        for _ in range(self.config.warmup_runs):
            self._run_single_inference(warmup_prompt)
        
        # 2. 内存基准测试
        print("  记录初始内存...")
        memory_before = self._get_memory_usage()
        gpu_memory_before = self._get_gpu_memory_usage()
        
        # 3. 多次运行收集数据
        print(f"  执行测试 ({self.config.num_runs} 次)...")
        latencies = []
        throughputs = []
        
        prompts = self.config.prompts if self.config.prompts else [self.config.prompt]
        run_count = 0
        
        for run_idx in range(self.config.num_runs):
            prompt = prompts[run_idx % len(prompts)]
            
            elapsed, tokens = self._run_single_inference(prompt)
            
            latencies.append(elapsed * 1000)  # 转换为毫秒
            throughputs.append(tokens / elapsed)  # tokens per second
            
            run_count += 1
            if run_count % 5 == 0:
                print(f"    已完成 {run_count}/{self.config.num_runs}")
        
        # 4. 计算统计指标
        print("  计算统计指标...")
        metrics = PerformanceMetrics()
        
        # 延迟统计
        metrics.latency_avg = float(np.mean(latencies))
        metrics.latency_p50 = float(np.percentile(latencies, 50))
        metrics.latency_p95 = float(np.percentile(latencies, 95))
        metrics.latency_p99 = float(np.percentile(latencies, 99))
        
        # 吞吐量统计
        metrics.throughput = float(np.mean(throughputs))
        
        # 内存统计
        memory_after = self._get_memory_usage()
        gpu_memory_after = self._get_gpu_memory_usage()
        
        metrics.memory_usage = memory_after
        metrics.gpu_memory_usage = gpu_memory_after
        
        # 详细统计
        latency_stats = {
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "std": float(np.std(latencies)),
            "cv": float(np.std(latencies) / np.mean(latencies)) if np.mean(latencies) > 0 else 0
        }
        
        memory_stats = {
            "cpu_delta": memory_after - memory_before,
            "gpu_delta": gpu_memory_after - gpu_memory_before,
        }
        
        # 5. 质量指标（可选）
        if self.config.measure_quality:
            metrics.perplexity = self._calculate_perplexity(prompts)
        
        print(f"  平均延迟: {metrics.latency_avg:.2f} ms")
        print(f"  P95 延迟: {metrics.latency_p95:.2f} ms")
        print(f"  吞吐量: {metrics.throughput:.2f} tokens/s")
        print(f"  GPU 内存: {metrics.gpu_memory_usage:.2f} MB")
        
        # 6. 生成结果
        result = BenchmarkResult(
            config=self.config,
            metrics=metrics,
            model_name=model_name,
            model_type=model_type,
            latency_stats=latency_stats,
            memory_stats=memory_stats,
            raw_latencies=latencies,
            raw_throughputs=throughputs,
        )
        
        print("基准测试完成!")
        return result


def compare_results(
    result1: BenchmarkResult,
    result2: BenchmarkResult,
    name1: str = "优化前",
    name2: str = "优化后",
) -> Dict[str, Any]:
    """
    对比两个基准测试结果
    
    Args:
        result1: 第一个结果
        result2: 第二个结果
        name1: 第一个结果名称
        name2: 第二个结果名称
        
    Returns:
        对比结果字典
    """
    m1 = result1.metrics
    m2 = result2.metrics
    
    def calc_change(old: float, new: float) -> Dict[str, float]:
        if old == 0:
            return {"absolute": new - old, "percent": 0.0}
        return {
            "absolute": new - old,
            "percent": ((new - old) / old * 100
        }
    
    comparison = {
        "models": {
            name1: result1.model_name,
            name2: result2.model_name,
        },
        "latency_ms": {
            name1: m1.latency_avg,
            name2: m2.latency_avg,
            "change": calc_change(m1.latency_avg, m2.latency_avg),
        },
        "latency_p95_ms": {
            name1: m1.latency_p95,
            name2: m2.latency_p95,
            "change": calc_change(m1.latency_p95, m2.latency_p95),
        },
        "throughput_tps": {
            name1: m1.throughput,
            name2: m2.throughput,
            "change": calc_change(m1.throughput, m2.throughput),
        },
        "gpu_memory_mb": {
            name1: m1.gpu_memory_usage,
            name2: m2.gpu_memory_usage,
            "change": calc_change(m1.gpu_memory_usage, m2.gpu_memory_usage),
        },
    }
    
    # 总结改进百分比
    summary = []
    if m1.latency_avg > 0:
        latency_improve = (m1.latency_avg - m2.latency_avg) / m1.latency_avg * 100
        summary.append(f"延迟改进: {latency_improve:+.2f}%")
    
    if m1.throughput > 0:
        throughput_improve = (m2.throughput - m1.throughput) / m1.throughput * 100
        summary.append(f"吞吐量改进: {throughput_improve:+.2f}%")
    
    if m1.gpu_memory_usage > 0:
        memory_improve = (m1.gpu_memory_usage - m2.gpu_memory_usage) / m1.gpu_memory_usage * 100
        summary.append(f"GPU 内存节省: {memory_improve:+.2f}%")
    
    comparison["summary"] = summary
    
    return comparison


def print_comparison(comparison: Dict[str, Any]) -> None:
    """
    打印对比结果
    
    Args:
        comparison: compare_results 输出
    """
    print("\n" + "=" * 60)
    print("  基准测试结果对比")
    print("=" * 60)
    
    name1, name2 = list(comparison["models"].keys())[:2]
    
    print(f"\n  {name1}: {comparison['models'][name1]}")
    print(f"  {name2}: {comparison['models'][name2]}")
    
    print("\n  性能指标:")
    
    for metric_name, metric_data in comparison.items():
        if metric_name in ["models", "summary"]:
            continue
        
        unit = metric_name.split("_")[-1]
        metric_display = " ".join(metric_name.split("_")[:-1]).replace("_", " ").title()
        
        v1 = metric_data[name1]
        v2 = metric_data[name2]
        change = metric_data["change"]
        
        print(f"\n    {metric_display}:")
        print(f"      {name1}: {v1:>10.2f} {unit}")
        print(f"      {name2}: {v2:>10.2f} {unit}")
        print(f"      变化: {change['absolute']:>+10.2f} {unit} ({change['percent']:+.2f}%)")
    
    print("\n  总结:")
    for item in comparison["summary"]:
        print(f"    - {item}")
    
    print("\n" + "=" * 60 + "\n")
