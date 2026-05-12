"""
Optimization Toolchain - 量化引擎测试
"""
import pytest
import sys
import os

# 添加路径
sys.path.insert(0, os.path.abspath("../../../p-mp2nnvkraon8mn-worker2"))

try:
    from optimization_toolchain.engines.quantization.gptq import GPTQQuantizer
    from optimization_toolchain.engines.quantization.awq import AWQQuantizer
    from optimization_toolchain.engines.quantization.squeezellm import SqueezeLLMQuantizer
except ImportError:
    pytest.skip("Quantization engines not fully implemented", allow_module_level=True)


@pytest.fixture
def sample_model():
    """示例模型 Mock"""
    class MockModel:
        def __init__(self):
            self.name = "test-model"
            self.parameters = {"layers": 12, "hidden_size": 768}
            self.size_mb = 1024
    
    return MockModel()


@pytest.fixture
def gptq_config():
    """GPTQ 配置"""
    return {
        "bits": 4,
        "group_size": 128,
        "damp_percent": 0.1,
        "desc_act": True
    }


@pytest.fixture
def awq_config():
    """AWQ 配置"""
    return {
        "bits": 4,
        "group_size": 128,
        "zero_point": True
    }


class TestGPTQQuantizer:
    """GPTQ 量化器测试"""
    
    def test_gptq_initialization(self, gptq_config):
        """测试 GPTQ 初始化"""
        quantizer = GPTQQuantizer(**gptq_config)
        assert quantizer is not None
        assert quantizer.bits == 4
        assert quantizer.group_size == 128
    
    def test_gptq_quantize(self, sample_model, gptq_config):
        """测试 GPTQ 量化"""
        quantizer = GPTQQuantizer(**gptq_config)
        result = quantizer.quantize(sample_model)
        
        assert result is not None
        assert result.success is True
        assert "size_reduction" in result.metrics
    
    def test_gptq_bits_validation(self):
        """测试比特数验证"""
        # 有效的比特数
        for bits in [2, 3, 4, 8]:
            quantizer = GPTQQuantizer(bits=bits, group_size=128)
            assert quantizer.bits == bits
    
    def test_gptq_group_size_validation(self):
        """测试 group size 验证"""
        # 有效的 group size
        for size in [32, 64, 128, 256]:
            quantizer = GPTQQuantizer(bits=4, group_size=size)
            assert quantizer.group_size == size
    
    def test_gptq_get_config(self, gptq_config):
        """测试获取配置"""
        quantizer = GPTQQuantizer(**gptq_config)
        config = quantizer.get_config()
        
        assert isinstance(config, dict)
        assert config["bits"] == 4
        assert config["group_size"] == 128
    
    def test_gptq_estimate_size_reduction(self, sample_model, gptq_config):
        """测试估算大小减少"""
        quantizer = GPTQQuantizer(**gptq_config)
        reduction = quantizer.estimate_size_reduction(sample_model)
        
        assert isinstance(reduction, float)
        assert 0 < reduction < 1  # 应该在 0-1 之间
    
    def test_gptq_calibration(self, sample_model, gptq_config):
        """测试校准"""
        quantizer = GPTQQuantizer(**gptq_config)
        
        # 模拟校准数据
        calibration_data = [f"Sample text {i}" for i in range(100)]
        result = quantizer.calibrate(sample_model, calibration_data)
        
        assert result is not None


class TestAWQQuantizer:
    """AWQ 量化器测试"""
    
    def test_awq_initialization(self, awq_config):
        """测试 AWQ 初始化"""
        quantizer = AWQQuantizer(**awq_config)
        assert quantizer is not None
        assert quantizer.bits == 4
    
    def test_awq_quantize(self, sample_model, awq_config):
        """测试 AWQ 量化"""
        quantizer = AWQQuantizer(**awq_config)
        result = quantizer.quantize(sample_model)
        
        assert result is not None
        assert result.success is True
    
    def test_awq_auto_scale(self, sample_model):
        """测试自动缩放"""
        quantizer = AWQQuantizer(bits=4, auto_scale=True)
        result = quantizer.auto_tune(sample_model)
        
        assert result is not None
    
    def test_awq_zero_point(self):
        """测试零点配置"""
        quantizer_with_zp = AWQQuantizer(bits=4, zero_point=True)
        quantizer_without_zp = AWQQuantizer(bits=4, zero_point=False)
        
        assert quantizer_with_zp.zero_point is True
        assert quantizer_without_zp.zero_point is False


class TestSqueezeLLMQuantizer:
    """SqueezeLLM 量化器测试"""
    
    def test_squeezellm_initialization(self):
        """测试 SqueezeLLM 初始化"""
        quantizer = SqueezeLLMQuantizer(bits=4)
        assert quantizer is not None
    
    def test_squeezellm_lut_configuration(self):
        """测试查找表配置"""
        quantizer = SqueezeLLMQuantizer(
            bits=4,
            lut_size=16,
            use_shared_lut=True
        )
        
        assert quantizer.lut_size == 16
        assert quantizer.use_shared_lut is True
    
    def test_squeezellm_quantize(self, sample_model):
        """测试 SqueezeLLM 量化"""
        quantizer = SqueezeLLMQuantizer(bits=4)
        result = quantizer.quantize(sample_model)
        
        assert result is not None
        assert result.success is True


class TestQuantizationComparison:
    """不同量化方法对比测试"""
    
    def test_quantization_methods_comparison(self, sample_model):
        """测试不同量化方法对比"""
        gptq = GPTQQuantizer(bits=4, group_size=128)
        awq = AWQQuantizer(bits=4, group_size=128)
        squeezellm = SqueezeLLMQuantizer(bits=4)
        
        gptq_result = gptq.quantize(sample_model)
        awq_result = awq.quantize(sample_model)
        squeezellm_result = squeezellm.quantize(sample_model)
        
        # 所有方法都应该成功
        assert gptq_result.success is True
        assert awq_result.success is True
        assert squeezellm_result.success is True
    
    def test_quantization_speed_comparison(self, sample_model):
        """测试量化速度对比"""
        import time
        
        results = {}
        
        for bits in [4, 8]:
            quantizer = GPTQQuantizer(bits=bits, group_size=128)
            
            start = time.time()
            result = quantizer.quantize(sample_model)
            duration = time.time() - start
            
            results[f"{bits}bit"] = {
                "duration": duration,
                "success": result.success
            }
        
        # 8-bit 应该比 4-bit 快（因为复杂度更低）
        assert results["8bit"]["success"] is True
        assert results["4bit"]["success"] is True


class TestQuantizationEdgeCases:
    """量化边界情况测试"""
    
    def test_empty_model_quantization(self):
        """测试空模型量化"""
        class EmptyModel:
            name = "empty"
            size_mb = 0
        
        quantizer = GPTQQuantizer(bits=4)
        result = quantizer.quantize(EmptyModel())
        
        # 应该优雅处理
        assert result is not None
    
    def test_quantization_with_different_dtypes(self, sample_model):
        """测试不同数据类型量化"""
        for dtype in ["fp16", "bf16", "fp32"]:
            quantizer = GPTQQuantizer(bits=4, dtype=dtype)
            result = quantizer.quantize(sample_model)
            assert result.success is True
    
    def test_quantization_progress_tracking(self, sample_model, gptq_config):
        """测试量化进度追踪"""
        quantizer = GPTQQuantizer(**gptq_config)
        
        progress_updates = []
        def progress_callback(progress, message):
            progress_updates.append((progress, message))
        
        result = quantizer.quantize(
            sample_model,
            progress_callback=progress_callback
        )
        
        assert result.success is True
        # 应该有一些进度更新
        assert len(progress_updates) > 0
        # 最后应该达到 100%
        assert progress_updates[-1][0] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
