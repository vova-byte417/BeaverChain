# 优化工具链集成模块 - Optimization Toolchain

> **任务 4: 集成多种大模型优化工具链，包括量化、蒸馏、vLLM、DeepSpeed 等引擎

## 项目概述

本模块为大模型构建系统提供统一的优化工具链集成，支持多种主流的模型压缩和推理加速技术。通过统一的接口封装了量化、知识蒸馏和高性能推理引擎，帮助用户轻松实现模型优化和部署。

### 核心特性

| 特性 | 描述 | 状态 |
|------|------|------|
| **量化 | GPTQ, AWQ, SqueezeLLM | ✅ 已实现 |
| **知识蒸馏** | 标准蒸馏、自蒸馏 | ✅ 已实现 |
| **推理引擎** | vLLM, DeepSpeed, TGI | ✅ 已实现 |
| **配置管理** | 统一配置接口 | ✅ 已实现 |
| **结果追踪** | 性能指标自动测量 | ✅ 已实现 |
| **单元测试** | 完整测试套件 | ✅ 已实现 |

---

## 模块结构

```
optimization_toolchain/
├── __init__.py                    # 包入口，导出所有主要类
├── requirements.txt               # 依赖列表
├── core/                          # 核心组件
│   ├── __init__.py
│   ├── base.py                  # 基类定义
│   ├── config.py                # 配置管理
│   └── result.py                # 结果数据类
├── engines/                       # 优化引擎实现
│   ├── __init__.py
│   ├── quantization/           # 量化引擎
│   │   ├── __init__.py
│   │   ├── base.py         # 量化基类
│   │   ├── gptq.py         # GPTQ 量化
│   │   ├── awq.py          # AWQ 量化
│   │   └── squeezellm.py   # SqueezeLLM 量化
│   ├── distillation/         # 蒸馏引擎
│   │   ├── __init__.py
│   │   ├── distiller.py    # 知识蒸馏器
│   │   ├── teacher.py      # 教师模型
│   │   └── student.py     # 学生模型
│   └── inference/            # 推理引擎
│       ├── __init__.py
│       ├── vllm_engine.py    # vLLM 推理引擎
│       ├── deepspeed_engine.py  # DeepSpeed 引擎
│       └── tgi_engine.py     # TGI (Text Generation Inference) 引擎
└── tests/                         # 测试套件
    ├── __init__.py
    ├── test_quantization.py   # 量化引擎测试
    ├── test_distillation.py   # 蒸馏引擎测试
    └── test_inference.py      # 推理引擎测试
```

---

## 快速开始

### 1. 安装依赖

```bash
# 基础依赖
pip install torch transformers accelerate datasets

# 安装所有优化工具链
cd optimization_toolchain
pip install -r requirements.txt
```

### 2. 量化示例

#### GPTQ 量化

```python
from optimization_toolchain import GPTQQuantizer, QuantizationConfig

# 配置量化
config = QuantizationConfig(
    name="my-model-gptq",
    method="gptq",
    bits=4,
    group_size=128,
    model_name_or_path="path/to/your/model",
    dataset="c4",
    seed=42,
)

# 创建量化器并执行
quantizer = GPTQQuantizer(config)
result = quantizer.quantize()

# 查看结果
print(f"量化成功: {result['success']}")
print(f"模型大小: {result['model_size_mb']:.2f} MB")
print(f"压缩比: {result['compression_ratio']:.2f}x")

# 保存量化模型
quantizer.save_quantized("./output/quantized_model")
```

#### AWQ 量化

```python
from optimization_toolchain import AWQQuantizer, QuantizationConfig

config = QuantizationConfig(
    name="my-model-awq",
    method="awq",
    bits=4,
    group_size=128,
    model_name_or_path="path/to/your/model",
    version="gemm",  # gemm/gemv
    auto_scale=True,
    auto_clip=True,
)

quantizer = AWQQuantizer(config)
result = quantizer.quantize()
```

### 3. 知识蒸馏示例

```python
from optimization_toolchain import KnowledgeDistiller, DistillationConfig, DistillationMode

# 配置蒸馏
config = DistillationConfig(
    name="knowledge-distill",
    teacher_model="large-model",
    student_model="small-model",
    mode=DistillationMode.STANDARD,
    temperature=2.0,
    alpha=0.7,  # 蒸馏损失权重
    num_epochs=5,
    batch_size=8,
    learning_rate=1e-4,
)

# 创建蒸馏器并执行
distiller = KnowledgeDistiller(config)
result = distiller.distill()

# 查看结果
print(f"蒸馏完成: {result['success']}")
print(f"最佳验证损失: {result['best_val_loss']:.4f}")
print(f"压缩比: {result['compression_ratio']:.2f}x")
```

### 4. 推理引擎示例

#### vLLM 高性能推理

```python
from optimization_toolchain import VLLMEngine, VLLMConfig

# 配置 vLLM
config = VLLMConfig(
    name="vllm-inference",
    model_name_or_path="path/to/your/model",
    tensor_parallel_size=2,  # 使用2张GPU
    gpu_memory_utilization=0.9,
    max_num_batched_tokens=4096,
)

# 创建引擎并优化
engine = VLLMEngine(config)
result = engine.optimize()

# 执行推理
prompts = [
    "Hello, what is machine learning?",
    "Explain quantum computing in simple terms:",
    "Write a poem about AI",
]

outputs = engine.generate(prompts, max_new_tokens=512, temperature=0.8)

for i, output in enumerate(outputs):
    print(f"\nPrompt {i+1}: {prompts[i]}")
    print(f"Response: {output['text']}")
```

#### DeepSpeed 推理

```python
from optimization_toolchain import DeepSpeedEngine, DeepSpeedConfig

config = DeepSpeedConfig(
    name="deepspeed-inference",
    model_name_or_path="path/to/your/model",
    zero_stage=3,
    use_kernel=True,
    max_tokens=2048,
    max_batch_size=16,
)

engine = DeepSpeedEngine(config)
result = engine.optimize()
outputs = engine.generate(["Hello, world!"])
```

#### TGI 生产级推理服务

```python
from optimization_toolchain import TGIEngine, TGIConfig

config = TGIConfig(
    name="tgi-service",
    model_name_or_path="path/to/your/model",
    num_shard=2,
    quantize="bitsandbytes-nf4",
    max_batch_total_tokens=8192,
    port=8080,
)

engine = TGIEngine(config)
result = engine.optimize()

# 单轮推理
result = engine.generate("Tell me about AI")

# 流式推理
for chunk in engine.generate_stream("Write a story"):
    print(chunk["text"], end="", flush=True)
```

---

## 核心概念

### 量化 (Quantization)

将高精度浮点数模型转换为低精度表示，显著减少显存占用，提升推理速度。

| 方法 | 精度 | 显存占用 | 推理速度 | 精度损失 |
|------|------|---------|---------|---------|
| **FP16** | 16位浮点数 | 100% | 基准 | 无 |
| **INT8** | 8位整数 | ~50% | ~1.5x | 很小 |
| **GPTQ 4bit** | 4位量化 | ~25% | ~3x | 小 |
| **AWQ 4bit** | 4位激活感知 | ~25% | ~3.5x | 很小 |
| **SqueezeLLM** | 4位非均匀 | ~25% | ~3x | 极小 |

### 知识蒸馏 (Knowledge Distillation)

让小模型(学生)学习大模型(教师)的输出分布，实现模型压缩。

**核心参数：
- **温度(Temperature)**: 控制教师输出分布的平滑程度
- **Alpha**: 蒸馏损失与原始损失的权重平衡
- **损失类型**: KL散度、MSE、余弦相似度等

### 推理引擎 (Inference Engines)

| 引擎 | 特点 | 最佳场景 |
|------|------|---------|
| **vLLM** | PagedAttention, 极高吞吐量 | 高并发批处理、服务部署 |
| **DeepSpeed** | ZeRO、FastGen | 超大规模模型、多GPU |
| **TGI** | 生产级服务、流式输出 | API服务部署、企业应用 |

---

## 详细文档

### 配置参考

#### QuantizationConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | str | 必填 | 配置名称 |
| `method` | str | "gptq" | 量化方法: gptq/awq/squeezellm |
| `bits` | int | 4 | 量化位数: 4/8 |
| `group_size` | int | 128 | 量化分组大小 |
| `desc_act` | bool | True | 使用激活排序 (GPTQ) |
| `model_name_or_path` | str | 必填 | 模型路径或名称 |
| `dataset` | str | "c4" | 校准数据集 |
| `seed` | int | 42 | 随机种子 |
| `output_dir` | str | "./output" | 输出目录 |

#### DistillationConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | str | 必填 | 配置名称 |
| `teacher_model` | str | 必填 | 教师模型路径 |
| `student_model` | str | 必填 | 学生模型路径 |
| `mode` | enum | STANDARD | 蒸馏模式 |
| `temperature` | float | 1.0 | 温度参数 |
| `alpha` | float | 0.5 | 蒸馏损失权重 |
| `num_epochs` | int | 3 | 训练轮数 |
| `batch_size` | int | 8 | 批次大小 |
| `learning_rate` | float | 1e-4 | 学习率 |

#### VLLMConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | str | 必填 | 配置名称 |
| `model_name_or_path` | str | 必填 | 模型路径 |
| `tensor_parallel_size` | int | 1 | 张量并行GPU数 |
| `gpu_memory_utilization` | float | 0.9 | GPU内存使用率 |
| `block_size` | int | 16 | PagedAttention块大小 |
| `max_num_batched_tokens` | int | 2048 | 最大批次token数 |
| `max_num_seqs` | int | 256 | 最大序列数 |

### 结果格式

所有优化引擎返回统一的结果格式：

```python
{
    "success": bool,           # 是否成功
    "name": str,              # 任务名称
    "model_name": str,         # 模型名称
    "config": dict,            # 使用的配置
    "execution_time": float,  # 执行时间(秒)
    "speedup": float,        # 相对加速比
    "memory_saving": float,   # 内存节省比例
    "metrics": {             # 详细性能指标
        "throughput": float,    # 吞吐量 tokens/秒
        "latency_p50": float,  # P50延迟
        "latency_p99": float,  # P99延迟
        "memory_peak_gb": float,   # 峰值内存(GB)
    },
    "output_path": str,      # 输出路径
}
```

---

## 性能基准测试

运行完整测试套件：

```bash
# 所有测试
pytest tests/ -v

# 仅量化测试
pytest tests/test_quantization.py -v

# 仅蒸馏测试
pytest tests/test_distillation.py -v

# 仅推理测试
pytest tests/test_inference.py -v

# 生成覆盖率报告
pytest tests/ -v --cov=optimization_toolchain --cov-report=html
```

---

## 常见问题

### Q: 如何选择量化方法？

- **追求最高吞吐量**: vLLM + AWQ
- **追求最小精度保留**: SqueezeLLM
- **通用场景**: GPTQ (最成熟，生态最好

### Q: 蒸馏温度参数如何设置？

- 一般推荐 `temperature=1~3
- 小模型用较高温度(1~5
- 大模型用较低温度(1~2)

### Q: 如何选择推理引擎？

| 场景 | 推荐引擎 |
|------|---------|
| 高吞吐量批处理 | vLLM |
| 70B+ 大模型 | DeepSpeed |
| API 服务部署 | TGI |
| 快速原型开发 | vLLM |

---

## 版本历史

- **v1.0.0** (2024-01-15)
  - 初始版本发布
  - 支持 GPTQ/AWQ/SqueezeLLM 量化
  - 支持知识蒸馏
  - 支持 vLLM/DeepSpeed/TGI 推理
  - 完整单元测试覆盖

---

## 许可证

MIT License

---

## 联系方式

- 项目地址: `projects/p-mp2nnvkraon8mn/
- 团队: BeaverChain Team
