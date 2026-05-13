# BeaverChain - 大模型构建系统

> **一站式大模型构建与运维平台** - 让每一个团队都能高效、可靠地构建和运维 AI 应用

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0--alpha-green.svg)](https://github.com/vova-byte417/BeaverChain/releases)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://github.com/vova-byte417/BeaverChain/wiki)
[![GitHub Stars](https://img.shields.io/github/stars/vova-byte417/BeaverChain)](https://github.com/vova-byte417/BeaverChain/stargazers)

---

## 🎯 核心特性

### 1. 版本化一切
- ✅ **模型权重版本管理** - 完整的权重快照和回滚
- ✅ **Prompt 版本控制** - Git 式分支、合并、对比
- ✅ **RAG 配置版本化** - 知识库、检索策略完整追踪
- ✅ **Guardrails 规则版本** - 安全规则变更可追溯
- ✅ **Lineage 完整追踪** - 从数据到输出的完整血缘链

### 2. 一体化工具链
- 🔧 **量化优化** - GPTQ/AWQ 量化一键集成
- 🧪 **知识蒸馏** - 模型压缩与性能优化
- ⚡ **vLLM 推理** - 高性能推理引擎集成
- 🚀 **DeepSpeed** - 分布式训练与推理

### 3. 可视化编排
- 🎨 **拖拽式设计器** - 无需编码构建复杂工作流
- 🔀 **条件分支** - 智能路由与逻辑判断
- 📦 **子工作流** - 模块化复用与嵌套
- 📊 **实时监控** - 执行状态可视化

### 4. 质量保障体系
- 📈 **幻觉率检测** - 自动识别与量化
- ☠️ **毒性评估** - 内容安全实时监控
- ✅ **忠实度评分** - 输出与输入一致性校验
- 🔔 **智能告警** - 异常指标自动通知

---

## 🚀 快速开始

### 前置要求

```bash
# 环境要求
- Python ≥ 3.10
- Node.js ≥ 18
- PostgreSQL ≥ 15
- Redis ≥ 7.0
- Docker & Docker Compose (推荐)
```

### 一键启动（Docker）

```bash
# 1. 克隆仓库
git clone https://github.com/vova-byte417/BeaverChain.git
cd BeaverChain

# 2. 复制配置文件
cp .env.example .env
# 编辑 .env 文件，配置数据库和 API 密钥

# 3. 启动所有服务
docker-compose up -d

# 4. 访问 Web 控制台
open http://localhost:3000

# 5. 默认登录
- 用户名: admin@beaverchain.ai
- 密码: admin123
```

### 本地开发环境

```bash
# 1. 后端服务启动
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 2. 前端服务启动
cd frontend
npm install
npm run dev

# 3. 访问
# 前端: http://localhost:5173
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

---

## 📚 文档索引

| 文档 | 描述 |
|------|------|
| [安装指南](docs/installation.md) | 详细的安装步骤和环境配置 |
| [快速入门教程](docs/quickstart.md) | 5 分钟上手核心功能 |
| [用户手册](docs/user-guide.md) | 完整功能使用说明 |
| [API 文档](docs/api/README.md) | REST API 参考文档 |
| [开发者文档](docs/developer/README.md) | 代码结构、贡献指南 |
| [测试说明](docs/testing.md) | 测试框架和运行指南 |
| [部署文档](docs/deployment.md) | 生产环境部署配置 |
| [常见问题 FAQ](docs/faq.md) | 常见问题解答 |
| [变更日志](CHANGELOG.md) | 版本更新记录 |
| [路线图](ROADMAP.md) | 未来功能规划 |

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web 控制台 (React + TS)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ 模型版本 │  │ Prompt   │  │ 编排引擎 │  │ 监控面板 │      │
│  │ 管理     │  │ 管理     │  │ Workflow │  │ 评估     │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API 网关 (Go + Gin)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ 认证授权    │  │ 限流熔断    │  │ 日志审计    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        微服务层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 版本控制服务 │  │ Prompt 服务  │  │ 编排服务     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 评估服务     │  │ 部署服务     │  │ Guardrails   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术选型 |
|------|---------|
| **前端** | React 18 + TypeScript + TailwindCSS v4 |
| | React Query + Zustand + React Flow |
| **后端** | Go 1.22 (API 服务) + Python 3.11 (ML 服务) |
| | Gin 框架 + FastAPI + gRPC |
| **数据库** | PostgreSQL 16 + Redis 7.0 + Milvus 2.3 |
| **存储** | MinIO / S3 兼容对象存储 |
| **部署** | Kubernetes + Argo Workflows |
| **监控** | Prometheus + Grafana + OpenTelemetry |

---

## 📖 使用示例

### 1. 创建第一个模型版本

```python
from beaverchain import ModelVersion

# 初始化客户端
client = beaverchain.Client(api_key="your-api-key")

# 创建模型版本
version = ModelVersion(
    name="my-first-model",
    description="我的第一个大模型版本",
    weights_path="./models/llama-2-7b",
    prompt_template="你是一个有帮助的 AI 助手...",
    rag_config={
        "knowledge_base": "docs",
        "top_k": 5
    }
)

# 保存版本
client.save_version(version)

# 查看版本历史
history = client.get_version_history("my-first-model")
```

### 2. 构建一个简单的 Workflow

```python
from beaverchain import Workflow, LLMNode, ConditionNode

# 创建工作流
wf = Workflow(name="customer-support")

# 添加节点
llm_node = LLMNode(
    model_version="my-first-model@v1.0",
    prompt="请分析用户问题的意图..."
)

condition_node = ConditionNode(
    condition="intent == 'technical'",
    if_branch="technical-support",
    else_branch="general-query"
)

# 连接节点
wf.connect(llm_node, condition_node)

# 执行工作流
result = wf.execute(user_query="我的服务器无法启动")
```

### 3. 查看评估指标

```python
# 获取模型质量报告
report = client.get_evaluation_report(
    model_name="my-first-model",
    time_range="7d"
)

print(f"幻觉率: {report.hallucination_rate:.2%}")
print(f"毒性评分: {report.toxicity_score:.3f}")
print(f"忠实度: {report.faithfulness_score:.2f}")
```

---

## 🧪 测试

BeaverChain 具有完整的测试覆盖：

```bash
# 运行所有测试
make test

# 运行单元测试
make test-unit

# 运行集成测试
make test-integration

# 运行 E2E 测试
make test-e2e

# 生成覆盖率报告
make coverage
```

- ✅ **单元测试覆盖率**: > 80%
- ✅ **集成测试**: 覆盖核心 API 流程
- ✅ **E2E 测试**: 覆盖关键用户场景
- ✅ **性能测试**: API 延迟 P95 < 500ms

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！请阅读 [贡献指南](docs/developer/CONTRIBUTING.md) 开始。

### 开发流程

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### 代码规范

- 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范
- 所有代码必须通过 lint 检查
- 新增功能必须包含单元测试
- 重大变更需要先提出 Issue 讨论

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙋‍♂️ 支持与联系

- 📧 **邮件**: support@beaverchain.ai
- 💬 **GitHub Issues**: [提交 Bug 或功能请求](https://github.com/vova-byte417/BeaverChain/issues)
- 📚 **文档**: [Wiki](https://github.com/vova-byte417/BeaverChain/wiki)
- 🔔 **更新通知**: Watch 本仓库获取最新动态

---

## ⭐ 项目统计

[![Stargazers over time](https://starchart.cc/vova-byte417/BeaverChain.svg)](https://starchart.cc/vova-byte417/BeaverChain)

---

## 💖 致谢

感谢以下开源项目对 BeaverChain 的启发和支持：

- [LangChain](https://github.com/langchain-ai/langchain)
- [LlamaIndex](https://github.com/run-llama/llama_index)
- [vLLM](https://github.com/vllm-project/vllm)
- [MLflow](https://github.com/mlflow/mlflow)
- [Weights & Biases](https://wandb.ai/)

---

**Made with ❤️ by the BeaverChain Team**

---

*最后更新: 2026-05-12*
*文档版本: v1.0*
