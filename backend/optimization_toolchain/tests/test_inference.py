"""
测试 - 推理引擎
"""
import pytest
import tempfile
import os

from ..engines.inference import (
    VLLMEngine,
    VLLMConfig,
    DeepSpeedEngine,
    DeepSpeedConfig,
    TGIEngine,
    TGIConfig,
)


class TestVLLMConfig:
    """测试 vLLM 配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = VLLMConfig(
            name="test-vllm",
            model_name_or_path="test-model",
        )
        assert config.tensor_parallel_size == 1
        assert config.gpu_memory_utilization == 0.9
        assert config.block_size == 16
        assert config.swap_space == 4
        assert config.max_num_batched_tokens == 2048
        assert config.max_num_seqs == 256
    
    def test_validate_config_valid(self):
        """测试有效配置验证"""
        config = VLLMConfig(
            name="test-valid",
            model_name_or_path="test-model",
            tensor_parallel_size=2,
            gpu_memory_utilization=0.85,
        )
        assert config.validate() is True
    
    def test_validate_config_invalid_memory(self):
        """测试无效内存配置"""
        config = VLLMConfig(
            name="test-invalid-memory",
            model_name_or_path="test-model",
            gpu_memory_utilization=1.5,  # 必须 <= 1
        )
        assert config.validate() is False
    
    def test_validate_config_invalid_parallel(self):
        """测试无效并行配置"""
        config = VLLMConfig(
            name="test-invalid-parallel",
            model_name_or_path="test-model",
            tensor_parallel_size=0,  # 必须 >= 1
        )
        assert config.validate() is False


class TestVLLMEngine:
    """测试 vLLM 引擎"""
    
    def test_init(self):
        """测试初始化"""
        config = VLLMConfig(
            name="test-vllm-init",
            model_name_or_path="test-model",
        )
        engine = VLLMEngine(config)
        assert engine is not None
        assert engine.config.name == "test-vllm-init"
    
    def test_optimize(self):
        """测试优化流程"""
        config = VLLMConfig(
            name="test-vllm-optimize",
            model_name_or_path="test-model",
        )
        engine = VLLMEngine(config)
        result = engine.optimize()
        assert result["success"] is True
        assert result["speedup"] >= 1.0
        assert result["memory_saving"] < 1.0
    
    def test_generate(self):
        """测试生成"""
        config = VLLMConfig(
            name="test-vllm-generate",
            model_name_or_path="test-model",
        )
        engine = VLLMEngine(config)
        engine.optimize()
        
        prompts = ["Hello, world!", "What is AI?"]
        results = engine.generate(prompts)
        assert len(results) == 2
        assert all("text" in r for r in results)
        assert all("finish_reason" in r for r in results)


class TestDeepSpeedConfig:
    """测试 DeepSpeed 配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = DeepSpeedConfig(
            name="test-deepspeed",
            model_name_or_path="test-model",
        )
        assert config.zero_stage == 3
        assert config.use_kernel is True
        assert config.dtype == "float16"
        assert config.cpu_offload is False
        assert config.max_tokens == 1024
        assert config.max_batch_size == 8
    
    def test_validate_config_valid(self):
        """测试有效配置"""
        config = DeepSpeedConfig(
            name="test-valid",
            model_name_or_path="test-model",
            zero_stage=2,
        )
        assert config.validate() is True
    
    def test_validate_config_invalid_stage(self):
        """测试无效 ZeRO stage"""
        config = DeepSpeedConfig(
            name="test-invalid-stage",
            model_name_or_path="test-model",
            zero_stage=4,  # 无效
        )
        assert config.validate() is False


class TestDeepSpeedEngine:
    """测试 DeepSpeed 引擎"""
    
    def test_init(self):
        """测试初始化"""
        config = DeepSpeedConfig(
            name="test-deepspeed-init",
            model_name_or_path="test-model",
        )
        engine = DeepSpeedEngine(config)
        assert engine is not None
    
    def test_optimize(self):
        """测试优化"""
        config = DeepSpeedConfig(
            name="test-deepspeed-optimize",
            model_name_or_path="test-model",
        )
        engine = DeepSpeedEngine(config)
        result = engine.optimize()
        assert result["success"] is True
        assert "speedup" in result
        assert "memory_saving" in result
    
    def test_ds_config_generation(self):
        """测试 DeepSpeed 配置生成"""
        config = DeepSpeedConfig(
            name="test-ds-config",
            model_name_or_path="test-model",
            zero_stage=3,
            cpu_offload=True,
        )
        engine = DeepSpeedEngine(config)
        ds_config = engine._build_ds_config()
        
        assert ds_config["zero_optimization"]["stage"] == 3
        assert ds_config["zero_optimization"]["offload_param"]["device"] == "cpu"
        assert ds_config["train_batch_size"] == 8


class TestTGIConfig:
    """测试 TGI 配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = TGIConfig(
            name="test-tgi",
            model_name_or_path="test-model",
        )
        assert config.num_shard == 1
        assert config.quantize is None
        assert config.max_batch_total_tokens == 4096
        assert config.max_input_length == 1024
        assert config.max_total_tokens == 2048
    
    def test_validate_config_valid(self):
        """测试有效配置"""
        config = TGIConfig(
            name="test-valid",
            model_name_or_path="test-model",
            port=8080,
        )
        assert config.validate() is True
    
    def test_validate_config_invalid_port(self):
        """测试无效端口"""
        config = TGIConfig(
            name="test-invalid-port",
            model_name_or_path="test-model",
            port=0,  # 无效
        )
        assert config.validate() is False


class TestTGIEngine:
    """测试 TGI 引擎"""
    
    def test_init(self):
        """测试初始化"""
        config = TGIConfig(
            name="test-tgi-init",
            model_name_or_path="test-model",
        )
        engine = TGIEngine(config)
        assert engine is not None
    
    def test_build_server_command(self):
        """测试服务启动命令构建"""
        config = TGIConfig(
            name="test-tgi-cmd",
            model_name_or_path="test-model",
            quantize="bitsandbytes-nf4",
        )
        engine = TGIEngine(config)
        cmd = engine._build_server_command()
        
        assert "text-generation-launcher" in cmd
        assert "--model-id test-model" in cmd
        assert "--quantize bitsandbytes-nf4" in cmd
    
    def test_generate(self):
        """测试生成"""
        config = TGIConfig(
            name="test-tgi-generate",
            model_name_or_path="test-model",
        )
        engine = TGIEngine(config)
        engine.optimize()
        
        result = engine.generate("Test prompt")
        assert "text" in result
        assert "tokens" in result
        assert "finish_reason" in result
    
    def test_generate_stream(self):
        """测试流式生成"""
        config = TGIConfig(
            name="test-tgi-stream",
            model_name_or_path="test-model",
        )
        engine = TGIEngine(config)
        engine.optimize()
        
        stream_results = list(engine.generate_stream("Test stream"))
        assert len(stream_results) > 0
        assert all("text" in r for r in stream_results)


class TestEngineComparison:
    """测试不同引擎的性能对比"""
    
    def test_vllm_vs_deepspeed(self):
        """测试 vLLM vs DeepSpeed 性能对比"""
        vllm_config = VLLMConfig(
            name="vllm-compare",
            model_name_or_path="test-model",
        )
        vllm_engine = VLLMEngine(vllm_config)
        vllm_result = vllm_engine.optimize()
        
        ds_config = DeepSpeedConfig(
            name="deepspeed-compare",
            model_name_or_path="test-model",
        )
        ds_engine = DeepSpeedEngine(ds_config)
        ds_result = ds_engine.optimize()
        
        # vLLM 通常应该有更高的吞吐量
        assert vllm_result["speedup"] >= ds_result["speedup"] * 0.8  # 允许一些差异
    
    def test_tgi_4bit_memory(self):
        """测试 TGI 4-bit 量化的内存节省"""
        config_4bit = TGIConfig(
            name="tgi-4bit",
            model_name_or_path="test-model",
            quantize="bitsandbytes-nf4",
        )
        engine_4bit = TGIEngine(config_4bit)
        result_4bit = engine_4bit.optimize()
        
        # 4-bit 应该比 fp16 节省约 75% 内存
        assert result_4bit["memory_saving"] <= 0.35


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
