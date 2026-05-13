"""
测试 - 量化引擎
"""
import pytest
import tempfile
import os

from ..engines.quantization import (
    GPTQQuantizer,
    AWQQuantizer,
    SqueezeLLMQuantizer,
    QuantizationConfig,
)


class TestQuantizationConfig:
    """测试量化配置"""
    
    def test_gptq_config_default(self):
        """测试 GPTQ 配置默认值"""
        config = QuantizationConfig(
            name="test-gptq",
            method="gptq",
            bits=4,
            group_size=128,
            model_name_or_path="test-model",
        )
        assert config.method == "gptq"
        assert config.bits == 4
        assert config.group_size == 128
        assert config.desc_act is True
    
    def test_awq_config_default(self):
        """测试 AWQ 配置默认值"""
        config = QuantizationConfig(
            name="test-awq",
            method="awq",
            bits=4,
            group_size=128,
            model_name_or_path="test-model",
        )
        assert config.method == "awq"
        assert config.bits == 4
        assert config.auto_scale is True
        assert config.auto_clip is True
    
    def test_squeezellm_config_default(self):
        """测试 SqueezeLLM 配置默认值"""
        config = QuantizationConfig(
            name="test-squeezellm",
            method="squeezellm",
            bits=4,
            model_name_or_path="test-model",
        )
        assert config.method == "squeezellm"
        assert config.use_non_uniform is True
    
    def test_validate_config_valid(self):
        """测试有效配置验证"""
        config = QuantizationConfig(
            name="test-valid",
            method="gptq",
            bits=4,
            group_size=128,
            model_name_or_path="test-model",
        )
        quantizer = GPTQQuantizer(config)
        assert quantizer.validate_config() is True
    
    def test_validate_config_invalid_bits(self):
        """测试无效位宽验证"""
        config = QuantizationConfig(
            name="test-invalid",
            method="gptq",
            bits=0,  # 无效
            group_size=128,
            model_name_or_path="test-model",
        )
        quantizer = GPTQQuantizer(config)
        assert quantizer.validate_config() is False


class TestGPTQQuantizer:
    """测试 GPTQ 量化器"""
    
    def test_init(self):
        """测试初始化"""
        config = QuantizationConfig(
            name="test-gptq-init",
            method="gptq",
            bits=4,
            group_size=128,
            model_name_or_path="test-model",
        )
        quantizer = GPTQQuantizer(config)
        assert quantizer is not None
        assert quantizer.config.bits == 4
        assert quantizer.config.method == "gptq"
    
    def test_quantize_basic(self):
        """测试基本量化流程"""
        config = QuantizationConfig(
            name="test-gptq-quantize",
            method="gptq",
            bits=4,
            group_size=128,
            model_name_or_path="test-model",
            quant_method="gptq",
        )
        quantizer = GPTQQuantizer(config)
        assert quantizer.quantize() is True
    
    def test_save_quantized(self):
        """测试保存量化模型"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = QuantizationConfig(
                name="test-save",
                method="gptq",
                bits=4,
                group_size=128,
                model_name_or_path="test-model",
                output_dir=tmpdir,
            )
            quantizer = GPTQQuantizer(config)
            quantizer.quantize()
            result_path = quantizer.save_quantized()
            assert os.path.exists(result_path)


class TestAWQQuantizer:
    """测试 AWQ 量化器"""
    
    def test_init(self):
        """测试初始化"""
        config = QuantizationConfig(
            name="test-awq-init",
            method="awq",
            bits=4,
            group_size=128,
            model_name_or_path="test-model",
        )
        quantizer = AWQQuantizer(config)
        assert quantizer is not None
        assert quantizer.config.version == "gemm"
    
    def test_auto_scale_default(self):
        """测试自动缩放默认值"""
        config = QuantizationConfig(
            name="test-auto-scale",
            method="awq",
            bits=4,
            group_size=128,
            model_name_or_path="test-model",
        )
        quantizer = AWQQuantizer(config)
        assert quantizer.config.auto_scale is True


class TestSqueezeLLMQuantizer:
    """测试 SqueezeLLM 量化器"""
    
    def test_init(self):
        """测试初始化"""
        config = QuantizationConfig(
            name="test-squeezellm-init",
            method="squeezellm",
            bits=4,
            group_size=64,
            model_name_or_path="test-model",
        )
        quantizer = SqueezeLLMQuantizer(config)
        assert quantizer is not None
        assert quantizer.config.use_non_uniform is True
    
    def test_lookup_config(self):
        """测试查找表配置"""
        config = QuantizationConfig(
            name="test-lookup",
            method="squeezellm",
            bits=4,
            group_size=64,
            model_name_or_path="test-model",
        )
        quantizer = SqueezeLLMQuantizer(config)
        assert hasattr(quantizer, '_lookup_table')


class TestQuantizationWorkflow:
    """测试完整量化工作流"""
    
    def test_full_quantization_workflow(self):
        """测试完整量化流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = QuantizationConfig(
                name="test-full-workflow",
                method="gptq",
                bits=4,
                group_size=128,
                model_name_or_path="test-model",
                output_dir=tmpdir,
                seed=42,
            )
            
            result = GPTQQuantizer.run_quantization(config)
            assert result["success"] is True
            assert result["model_name"] == "test-full-workflow"
            assert result["config"]["method"] == "gptq"
            assert result["config"]["bits"] == 4
            assert "output_path" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
