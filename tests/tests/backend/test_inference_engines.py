"""
Optimization Toolchain - 推理引擎测试
"""
import pytest
import sys
import os

# 添加路径
sys.path.insert(0, os.path.abspath("../../../p-mp2nnvkraon8mn-worker2"))

try:
    from optimization_toolchain.engines.inference.vllm_engine import VLLMEngine
    from optimization_toolchain.engines.inference.deepspeed_engine import DeepSpeedEngine
    from optimization_toolchain.engines.inference.tgi_engine import TGIEngine
except ImportError:
    pytest.skip("Inference engines not fully implemented", allow_module_level=True)


@pytest.fixture
def sample_model_path():
    """示例模型路径"""
    return "/path/to/model"


@pytest.fixture
def vllm_config():
    """vLLM 配置"""
    return {
        "tensor_parallel_size": 1,
        "dtype": "fp16",
        "max_model_len": 2048,
        "gpu_memory_utilization": 0.9
    }


@pytest.fixture
def deepspeed_config():
    """DeepSpeed 配置"""
    return {
        "tensor_parallel_size": 1,
        "stage": 3,
        "offload": True
    }


@pytest.fixture
def tgi_config():
    """TGI 配置"""
    return {
        "max_batch_size": 32,
        "max_concurrent_requests": 128,
        "quantize": None
    }


class TestVLLMEngine:
    """vLLM 引擎测试"""
    
    def test_vllm_initialization(self, sample_model_path, vllm_config):
        """测试 vLLM 初始化"""
        engine = VLLMEngine(
            model_path=sample_model_path,
            **vllm_config
        )
        
        assert engine is not None
        assert engine.tensor_parallel_size == 1
        assert engine.dtype == "fp16"
    
    def test_vllm_generate(self, sample_model_path, vllm_config):
        """测试 vLLM 生成"""
        engine = VLLMEngine(model_path=sample_model_path, **vllm_config)
        
        prompt = "Hello, how are you?"
        result = engine.generate(
            prompt=prompt,
            max_tokens=50,
            temperature=0.7
        )
        
        assert result is not None
        assert "text" in result
        assert "tokens" in result
    
    def test_vllm_batch_generate(self, sample_model_path, vllm_config):
        """测试 vLLM 批量生成"""
        engine = VLLMEngine(model_path=sample_model_path, **vllm_config)
        
        prompts = [
            "What is AI?",
            "Explain machine learning",
            "Tell me about deep learning"
        ]
        
        results = engine.batch_generate(
            prompts=prompts,
            max_tokens=50
        )
        
        assert len(results) == len(prompts)
        for result in results:
            assert "text" in result
    
    def test_vllm_throughput_measurement(self, sample_model_path, vllm_config):
        """测试 vLLM 吞吐量测量"""
        engine = VLLMEngine(model_path=sample_model_path, **vllm_config)
        
        throughput = engine.measure_throughput(
            num_requests=10,
            max_tokens_per_request=32
        )
        
        assert isinstance(throughput, float)
        assert throughput > 0
    
    def test_vllm_latency_measurement(self, sample_model_path, vllm_config):
        """测试 vLLM 延迟测量"""
        engine = VLLMEngine(model_path=sample_model_path, **vllm_config)
        
        latency = engine.measure_latency(
            prompt="Test prompt",
            max_tokens=32,
            num_runs=5
        )
        
        assert isinstance(latency, dict)
        assert "avg" in latency
        assert "p50" in latency
        assert "p95" in latency
        assert "p99" in latency
    
    def test_vllm_memory_usage(self, sample_model_path, vllm_config):
        """测试 vLLM 内存使用"""
        engine = VLLMEngine(model_path=sample_model_path, **vllm_config)
        
        memory_stats = engine.get_memory_usage()
        
        assert isinstance(memory_stats, dict)
        assert "gpu_memory_used_mb" in memory_stats
        assert "cpu_memory_used_mb" in memory_stats
    
    def test_vllm_supported_models(self):
        """测试 vLLM 支持的模型列表"""
        supported = VLLMEngine.get_supported_models()
        
        assert isinstance(supported, list)
        assert len(supported) > 0
        assert any("llama" in m.lower() for m in supported)


class TestDeepSpeedEngine:
    """DeepSpeed 引擎测试"""
    
    def test_deepspeed_initialization(self, sample_model_path, deepspeed_config):
        """测试 DeepSpeed 初始化"""
        engine = DeepSpeedEngine(
            model_path=sample_model_path,
            **deepspeed_config
        )
        
        assert engine is not None
        assert engine.stage == 3
        assert engine.offload is True
    
    def test_deepspeed_inference(self, sample_model_path, deepspeed_config):
        """测试 DeepSpeed 推理"""
        engine = DeepSpeedEngine(model_path=sample_model_path, **deepspeed_config)
        
        result = engine.infer(
            prompt="What is DeepSpeed?",
            max_new_tokens=32
        )
        
        assert result is not None
        assert "output" in result
    
    def test_deepspeed_benchmark(self, sample_model_path, deepspeed_config):
        """测试 DeepSpeed 基准测试"""
        engine = DeepSpeedEngine(model_path=sample_model_path, **deepspeed_config)
        
        benchmark_result = engine.run_benchmark(
            batch_sizes=[1, 2, 4, 8],
            sequence_lengths=[128, 256, 512]
        )
        
        assert isinstance(benchmark_result, dict)
        assert "throughput" in benchmark_result
        assert "latency" in benchmark_result
    
    def test_deepspeed_zero_stages(self, sample_model_path):
        """测试不同 ZeRO 阶段"""
        for stage in [1, 2, 3]:
            engine = DeepSpeedEngine(
                model_path=sample_model_path,
                stage=stage
            )
            
            assert engine.stage == stage
            
            # 每个阶段都应该可以运行
            result = engine.infer(prompt="Test", max_new_tokens=8)
            assert result is not None


class TestTGIEngine:
    """Text Generation Inference 引擎测试"""
    
    def test_tgi_initialization(self, sample_model_path, tgi_config):
        """测试 TGI 初始化"""
        engine = TGIEngine(
            model_path=sample_model_path,
            **tgi_config
        )
        
        assert engine is not None
        assert engine.max_batch_size == 32
    
    def test_tgi_generate(self, sample_model_path, tgi_config):
        """测试 TGI 生成"""
        engine = TGIEngine(model_path=sample_model_path, **tgi_config)
        
        result = engine.generate(
            prompt="Explain TGI:",
            max_new_tokens=64,
            do_sample=True,
            temperature=0.8
        )
        
        assert result is not None
        assert "generated_text" in result
    
    def test_tgi_streaming(self, sample_model_path, tgi_config):
        """测试 TGI 流式生成"""
        engine = TGIEngine(model_path=sample_model_path, **tgi_config)
        
        chunks = []
        for chunk in engine.generate_stream(
            prompt="Count from 1 to 10:",
            max_new_tokens=32
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_text = "".join(chunks)
        assert len(full_text) > 0
    
    def test_tgi_health_check(self, sample_model_path, tgi_config):
        """测试 TGI 健康检查"""
        engine = TGIEngine(model_path=sample_model_path, **tgi_config)
        
        health = engine.health_check()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert "model_loaded" in health


class TestInferenceComparison:
    """推理引擎对比测试"""
    
    def test_all_engines_generate(self, sample_model_path, vllm_config, deepspeed_config, tgi_config):
        """测试所有引擎都能生成"""
        engines = [
            ("vLLM", VLLMEngine(model_path=sample_model_path, **vllm_config)),
            ("DeepSpeed", DeepSpeedEngine(model_path=sample_model_path, **deepspeed_config)),
            ("TGI", TGIEngine(model_path=sample_model_path, **tgi_config))
        ]
        
        for name, engine in engines:
            result = engine.generate(prompt=f"Test {name}", max_tokens=16)
            assert result is not None, f"{name} failed to generate"
    
    def test_throughput_comparison(self, sample_model_path):
        """测试不同引擎吞吐量对比"""
        configs = {"max_tokens": 32, "num_requests": 10}
        
        vllm = VLLMEngine(model_path=sample_model_path)
        vllm_throughput = vllm.measure_throughput(**configs)
        
        tgi = TGIEngine(model_path=sample_model_path)
        tgi_throughput = tgi.measure_throughput(**configs)
        
        # 两个都应该有正值
        assert vllm_throughput > 0
        assert tgi_throughput > 0


class TestInferenceEdgeCases:
    """推理引擎边界情况测试"""
    
    def test_empty_prompt(self, sample_model_path):
        """测试空 prompt"""
        engine = VLLMEngine(model_path=sample_model_path)
        
        result = engine.generate(prompt="", max_tokens=10)
        
        # 应该优雅处理
        assert result is not None
    
    def test_very_long_prompt(self, sample_model_path):
        """测试超长 prompt"""
        engine = VLLMEngine(model_path=sample_model_path)
        
        long_prompt = "This is a test. " * 100
        result = engine.generate(prompt=long_prompt, max_tokens=10)
        
        # 应该截断或优雅处理
        assert result is not None
    
    def test_zero_max_tokens(self, sample_model_path):
        """测试 0 max_tokens"""
        engine = VLLMEngine(model_path=sample_model_path)
        
        result = engine.generate(prompt="Test", max_tokens=0)
        
        # 应该返回空结果或仅输入
        assert result is not None
    
    def test_extreme_temperature(self, sample_model_path):
        """测试极端温度值"""
        engine = VLLMEngine(model_path=sample_model_path)
        
        # 非常低的温度（确定性）
        result_low = engine.generate(prompt="Test", max_tokens=10, temperature=0.001)
        assert result_low is not None
        
        # 非常高的温度（随机性）
        result_high = engine.generate(prompt="Test", max_tokens=10, temperature=100.0)
        assert result_high is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
