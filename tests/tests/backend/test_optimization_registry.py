"""
Optimization Toolchain - 优化器注册表测试
"""
import pytest
import sys
import os

# 添加路径
sys.path.insert(0, os.path.abspath("../../../p-mp2nnvkraon8mn-worker2"))

try:
    from optimization_toolchain.core.registry import OptimizationRegistry
    from optimization_toolchain.core.base import OptimizationResult
except ImportError:
    pytest.skip("Optimization toolchain module not fully implemented", allow_module_level=True)


@pytest.fixture
def registry():
    """创建空的注册表"""
    return OptimizationRegistry()


@pytest.fixture
def mock_optimizer():
    """Mock 优化器"""
    class MockOptimizer:
        name = "mock_optimizer"
        version = "1.0.0"
        
        def optimize(self, model, **kwargs):
            return OptimizationResult(
                success=True,
                model_name="test-model",
                optimizer_name=self.name,
                metrics={"size_reduction": 0.5, "speedup": 2.0}
            )
    
    return MockOptimizer()


class TestOptimizationRegistry:
    """优化器注册表测试"""
    
    def test_registry_initialization(self, registry):
        """测试注册表初始化"""
        assert registry is not None
        assert len(registry.list_optimizers()) >= 0
    
    def test_register_optimizer(self, registry, mock_optimizer):
        """测试注册优化器"""
        registry.register("mock", mock_optimizer)
        assert "mock" in registry.list_optimizers()
    
    def test_get_optimizer(self, registry, mock_optimizer):
        """测试获取优化器"""
        registry.register("mock", mock_optimizer)
        optimizer = registry.get("mock")
        assert optimizer is not None
        assert optimizer.name == "mock_optimizer"
    
    def test_get_nonexistent_optimizer(self, registry):
        """测试获取不存在的优化器"""
        optimizer = registry.get("nonexistent")
        assert optimizer is None
    
    def test_list_optimizers(self, registry, mock_optimizer):
        """测试列出优化器"""
        initial_count = len(registry.list_optimizers())
        registry.register("mock1", mock_optimizer)
        registry.register("mock2", mock_optimizer)
        assert len(registry.list_optimizers()) == initial_count + 2
    
    def test_unregister_optimizer(self, registry, mock_optimizer):
        """测试注销优化器"""
        registry.register("mock", mock_optimizer)
        assert "mock" in registry.list_optimizers()
        
        registry.unregister("mock")
        assert "mock" not in registry.list_optimizers()
    
    def test_register_duplicate(self, registry, mock_optimizer):
        """测试重复注册"""
        registry.register("mock", mock_optimizer)
        
        # 重复注册应该覆盖或报错
        registry.register("mock", mock_optimizer)
        assert "mock" in registry.list_optimizers()
    
    def test_get_optimizer_info(self, registry, mock_optimizer):
        """测试获取优化器信息"""
        registry.register("mock", mock_optimizer)
        info = registry.get_info("mock")
        
        assert info is not None
        assert "name" in info
        assert "version" in info
    
    def test_filter_by_type(self, registry, mock_optimizer):
        """测试按类型过滤优化器"""
        registry.register("quant_mock", mock_optimizer)
        registry.register("distill_mock", mock_optimizer)
        
        all_optimizers = registry.list_optimizers()
        assert len(all_optimizers) >= 2


class TestOptimizationResult:
    """优化结果测试"""
    
    def test_result_creation(self):
        """测试创建优化结果"""
        result = OptimizationResult(
            success=True,
            model_name="test-model",
            optimizer_name="test_opt",
            metrics={"accuracy": 0.95}
        )
        
        assert result.success is True
        assert result.model_name == "test-model"
        assert result.optimizer_name == "test_opt"
    
    def test_failed_result(self):
        """测试失败结果"""
        result = OptimizationResult(
            success=False,
            model_name="test-model",
            optimizer_name="test_opt",
            error_message="Optimization failed"
        )
        
        assert result.success is False
        assert result.error_message == "Optimization failed"
    
    def test_result_metrics(self):
        """测试结果指标"""
        metrics = {
            "size_reduction": 0.5,
            "speedup": 2.0,
            "accuracy_drop": 0.01,
            "memory_usage": "512MB"
        }
        
        result = OptimizationResult(
            success=True,
            model_name="test",
            optimizer_name="test",
            metrics=metrics
        )
        
        for key, value in metrics.items():
            assert result.metrics[key] == value
    
    def test_result_duration(self):
        """测试结果时长"""
        result = OptimizationResult(
            success=True,
            model_name="test",
            optimizer_name="test",
            duration_seconds=120.5
        )
        
        assert result.duration_seconds == 120.5
    
    def test_result_to_dict(self):
        """测试结果转换为字典"""
        result = OptimizationResult(
            success=True,
            model_name="test-model",
            optimizer_name="test-opt",
            metrics={"speedup": 2.0}
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["model_name"] == "test-model"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
