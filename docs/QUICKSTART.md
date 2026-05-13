# 快速开始指南

本文档将帮助您在 5 分钟内快速上手 BeaverChain 平台。

## 🚀 5分钟快速启动

### 前置条件检查

在开始之前，请确保您的系统满足以下要求：

| 软件 | 版本要求 | 检查命令 |
|------|---------|---------|
| Python | ≥ 3.10 | `python3 --version` |
| Node.js | ≥ 18.0 | `node --version` |
| Docker | ≥ 24.0 | `docker --version` |
| Git | ≥ 2.0 | `git --version` |

### 第一步：克隆仓库

```bash
# 克隆项目
git clone https://github.com/vova-byte417/BeaverChain.git
cd BeaverChain

# 确认当前目录
pwd  # 应该显示 BeaverChain 项目路径
```

### 第二步：环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env  # 或使用您喜欢的编辑器
```

**必填配置项：**
```env
# 数据库配置
DATABASE_URL=sqlite:///./beaverchain.db

# Redis 配置（可选，用于任务队列）
REDIS_URL=redis://localhost:6379/0

# 模型 API 配置
OPENAI_API_KEY=your_openai_key_here
ARK_API_KEY=your_ark_key_here
```

### 第三步：安装依赖

```bash
# 安装 Python 后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 第四步：启动服务

#### 方式一：使用 Docker Compose（推荐）

```bash
# 一键启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 方式二：手动启动开发环境

```bash
# 启动后端服务（终端 1）
python main.py

# 启动前端服务（终端 2）
cd frontend
npm run dev
```

### 第五步：验证安装

打开浏览器访问：
- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 🎯 第一个模型部署

### 1. 注册模型

```python
from beaverchain import ModelRegistry

registry = ModelRegistry()

# 注册一个基础模型
model = registry.register(
    name="llama2-7b-chat",
    source="huggingface",
    path="meta-llama/Llama-2-7b-chat-hf"
)

print(f"模型注册成功: {model.id}")
```

### 2. 应用量化优化

```python
from beaverchain.optimization import Quantizer

quantizer = Quantizer()

# 应用 4-bit AWQ 量化
optimized_model = quantizer.apply(
    model_id=model.id,
    method="awq",
    bits=4,
    device="cuda"
)

print(f"量化完成: {optimized_model.size}")
```

### 3. 部署模型

```python
from beaverchain.deployment import Deployer

deployer = Deployer()

# 部署到 vLLM 引擎
deployment = deployer.deploy(
    model_id=optimized_model.id,
    engine="vllm",
    gpu_count=1,
    tensor_parallel_size=1
)

print(f"部署成功，端点: {deployment.endpoint}")
```

### 4. 测试推理

```python
import requests

response = requests.post(
    f"{deployment.endpoint}/generate",
    json={
        "prompt": "什么是大语言模型？",
        "max_tokens": 512,
        "temperature": 0.7
    }
)

print(response.json()["text"])
```

## 🧪 第一个测试用例

### 运行单元测试

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定模块测试
pytest tests/unit/test_model_registry.py -v

# 生成覆盖率报告
pytest tests/unit/ --cov=core --cov-report=html
```

### 运行集成测试

```bash
# 运行 API 集成测试
pytest tests/integration/test_api.py -v
```

## 📊 监控第一个工作流

### 创建工作流

```python
from beaverchain.orchestration import Workflow, Executor

# 定义工作流
workflow = Workflow(name="text-generation-pipeline")
workflow.add_step("load_model", model_id="llama2-7b")
workflow.add_step("quantize", method="awq")
workflow.add_step("deploy", engine="vllm")

# 执行工作流
executor = Executor()
result = executor.run(workflow)

print(f"工作流状态: {result.status}")
```

### 查看监控面板

访问 http://localhost:3000/dashboard 查看：
- 实时资源使用率
- 模型推理延迟
- Token 消耗统计
- 任务队列状态

## 🔧 常用命令速查

### 项目管理

```bash
# 启动所有服务
make up

# 停止所有服务
make down

# 查看日志
make logs

# 重启服务
make restart
```

### 数据库操作

```bash
# 初始化数据库
python -m scripts.init_db

# 创建迁移
python -m scripts.make_migration

# 执行迁移
python -m scripts.migrate
```

### 测试命令

```bash
# 运行所有测试
make test

# 运行特定类型测试
make test-unit
make test-integration
make test-e2e

# 代码质量检查
make lint
```

## 🎓 下一步学习

1. **深入了解核心概念** - 阅读 [ARCHITECTURE.md](./architecture/ARCHITECTURE.md)
2. **学习 API 使用** - 查看 [API 文档](./API.md)
3. **掌握部署配置** - 参考 [部署指南](./DEPLOYMENT.md)
4. **了解开发规范** - 阅读 [开发规范](./DEVELOPMENT.md)
5. **配置监控告警** - 参考监控模块文档

## ❓ 遇到问题？

如果在快速开始过程中遇到问题：

1. 查看 [故障排查指南](./TROUBLESHOOTING.md)
2. 检查常见问题 FAQ
3. 在 GitHub 提交 Issue
4. 联系技术支持团队

---

**恭喜！您已完成 BeaverChain 快速入门。现在可以开始构建您的大模型应用了！** 🎉
