"""
优化工具链 (Optimization Toolchain)
=====================================

大模型优化工具链集成模块，集成多种主流优化技术。

## 主要功能

### 1. 量化 (Quantization)
- **GPTQ**: 生成式预训练量化，4-bit/8-bit 量化
- **AWQ**: 激活感知权重量化，显存优化
- **SqueezeLLM**: 基于敏感度的非均匀量化
- 支持 INT4/INT8/FP8 多种精度

### 2. 知识蒸馏 (Distillation)
- **标准蒸馏**: 大模型教小模型
- **自蒸馏**: 模型自己教自己
- **特征蒸馏**: 基于隐层特征的蒸馏
- 支持多温度缩放、注意力蒸馏

### 3. 推理引擎 (Inference)
- **vLLM**: PagedAttention 高吞吐量推理
- **DeepSpeed**: 微软大规模推理优化
- **TGI**: Text Generation Inference 生产级推理服务

## 快速开始

```python
from optimization_toolchain import (
    GPTQQuantizer,
    KnowledgeDistiller,
    VLLMEngine,
    QuantizationConfig,
    DistillationConfig,
    VLLMConfig,
)

# GPTQ 量化
quant_config = QuantizationConfig(
    name="my-model-gptq",
    method="gptq",
    bits=4,
    group_size=128,
    model_name_or_path="my-model",
)
quantizer = GPTQQuantizer(quant_config)
result = quantizer.quantize()

# 知识蒸馏
distill_config = DistillationConfig(
    name="my-distill",
    teacher_model="large-model",
    student_model="small-model",
    temperature=2.0,
    alpha=0.7,
    num_epochs=5,
)
distiller = KnowledgeDistiller(distill_config)
result = distiller.distill()

# vLLM 推理
infer_config = VLLMConfig(
    name="my-inference",
    model_name_or_path="my-model",
    tensor_parallel_size=2,
)
engine = VLLMEngine(infer_config)
result = engine.optimize()
outputs = engine.generate(["Hello, world!"])
```

## 模块结构

```
optimization_toolchain/
├── core/                      # 核心组件
│   ├── base.py               # 基类定义
│   ├── config.py             # 配置管理
│   └── result.py             # 结果数据类
├── engines/                   # 优化引擎
│   ├── quantization/         # 量化引擎
│   │   ├── gptq.py
│   │   ├── awq.py
│   │   └── squeezellm.py
│   ├── distillation/         # 蒸馏引擎
│   │   ├── distiller.py
│   │   ├── teacher.py
│   │   └── student.py
│   └── inference/            # 推理引擎
│       ├── vllm_engine.py
│       ├── deepspeed_engine.py
│       └── tgi_engine.py
├── tests/                    # 测试模块
│   ├── test_quantization.py
│   ├── test_distillation.py
│   └── test_inference.py
├── requirements.txt           # 依赖列表
└── README.md                 # 本文件
```

## 依赖安装

### 基础依赖
```bash
pip install torch transformers accelerate datasets
```

### 量化依赖
```bash
# GPTQ
pip install auto-gptq optimum[gptq]

# AWQ
pip install autoawq

# SqueezeLLM
pip install squeezellm
```

### 推理依赖
```bash
# vLLM
pip install vllm

# DeepSpeed
pip install deepspeed

# TGI
pip install text-generation
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 仅运行量化测试
pytest tests/test_quantization.py -v

# 仅运行蒸馏测试
pytest tests/test_distillation.py -v

# 仅运行推理测试
pytest tests/test_inference.py -v
```

## 技术文档

### 量化流程
1. 加载模型和分词器
2. 准备校准数据集
3. 执行量化算法
4. 验证精度和速度
5. 保存量化模型

### 蒸馏流程
1. 加载教师和学生模型
2. 准备训练数据集
3. 配置损失函数和优化器
4. 执行蒸馏训练
5. 验证学生模型性能
6. 保存蒸馏后的学生模型

### 推理优化流程
1. 加载推理引擎配置
2. 初始化推理引擎
3. 执行性能基准测试
4. 生成优化报告
5. 保存配置

## 版本历史

- **v1.0.0** (2024-01-15)
  - 初始版本
  - 支持 GPTQ/AWQ/SqueezeLLM 量化
  - 支持知识蒸馏
  - 支持 vLLM/DeepSpeed/TGI 推理
  - 完整的单元测试

## 许可证

MIT License

## 作者

BeaverChain Team

"""

__version__ = "1.0.0"
__author__ = "BeaverChain Team"

# 核心组件
from .core import (
    BaseOptimizer,
    OptimizationConfig,
    OptimizationResult,
    PerformanceMetrics,
    OptimizationType,
    QuantizationMethod,
    DistillationMode,
    DistillationLossType,
)

# 量化引擎
from .engines.quantization import (
    BaseQuantizer,
    QuantizationConfig,
    GPTQQuantizer,
    AWQQuantizer,
    SqueezeLLMQuantizer,
)

# 蒸馏引擎
from .engines.distillation import (
    KnowledgeDistiller,
    DistillationConfig,
    DistillationResult,
    DistillationMode,
    DistillationLossType,
    TeacherModel,
    StudentModel,
    TeacherConfig,
    StudentConfig,
)

# 推理引擎
from .engines.inference import (
    VLLMEngine,
    VLLMConfig,
    DeepSpeedEngine,
    DeepSpeedConfig,
    TGIEngine,
    TGIConfig,
)

__all__ = [
    # 核心
    "BaseOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "PerformanceMetrics",
    "OptimizationType",
    "QuantizationMethod",
    "DistillationMode",
    "DistillationLossType",
    
    # 量化
    "BaseQuantizer",
    "QuantizationConfig",
    "GPTQQuantizer",
    "AWQQuantizer",
    "SqueezeLLMQuantizer",
    
    # 蒸馏
    "KnowledgeDistiller",
    "DistillationConfig",
    "DistillationResult",
    "TeacherModel",
    "StudentModel",
    "TeacherConfig",
    "StudentConfig",
    
    # 推理
    "VLLMEngine",
    "VLLMConfig",
    "DeepSpeedEngine",
    "DeepSpeedConfig",
    "TGIEngine",
    "TGIConfig",
]
