# BeaverChain 系统架构设计文档

## 📁 文档目录

| 文件名 | 说明 |
|--------|------|
| **ARCHITECTURE.md** | 系统架构总览 - 整体架构设计、模块划分、技术栈 |
| **API-SPEC.md** | API 接口规范 - 完整的 REST API 设计、示例、SDK 使用 |
| **DATABASE-DESIGN.md** | 数据库设计 - ER 图、表结构、Redis/Milvus 设计 |
| **TECH-STACK.md** | 技术选型说明 - 各技术选型理由、对比分析、演进路线 |

---

## 🏗️ 架构总览

### 核心设计原则

1. **模块化** - 微服务架构，每个模块独立部署独立扩展
2. **API 优先** - 所有功能通过 API 暴露，支持多语言 SDK
3. **云原生** - Kubernetes 原生设计，弹性伸缩
4. **可观测性** - 统一的日志、监控、追踪体系

### 系统分层

```
┌─────────────────────────────────────────────────────────┐
│  客户端层 (Web UI / Python SDK / JS SDK / CLI)          │
├─────────────────────────────────────────────────────────┤
│  API 网关层 (认证、限流、路由、日志审计)                  │
├─────────────────────────────────────────────────────────┤
│  微服务层                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Model    │ │ Prompt   │ │ RAG      │ │ Workflow │  │
│  │ Registry │ │ Engine   │ │ Engine   │ │ Orchestr │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │ Evaluat- │ │ Guard-   │ │ Deploy-  │                │
│  │ ion Suite│ │ rails    │ │ ment Mgr │                │
│  └──────────┘ └──────────┘ └──────────┘                │
├─────────────────────────────────────────────────────────┤
│  数据层 (PostgreSQL + Redis + Milvus + MinIO)          │
├─────────────────────────────────────────────────────────┤
│  基础设施层 (Kubernetes + Helm + ArgoCD + Prometheus)   │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 核心模块说明

### 1. Model Registry (模型版本化)
- **职责**: 模型版本的 CRUD、快照、回滚、血缘追踪
- **技术栈**: Go + Gin + PostgreSQL
- **核心功能**:
  - 多维度版本管理（权重、Prompt、RAG 配置、Guardrails）
  - 版本对比可视化
  - 完整 Lineage 血缘追踪

### 2. Prompt Engine (提示词引擎)
- **职责**: Prompt 版本化、分支管理、测试预览、变量解析
- **技术栈**: Go + Gin + PostgreSQL + Redis
- **核心功能**:
  - 富文本编辑器，变量高亮
  - Git 风格分支合并
  - 实时测试预览效果

### 3. Optimization Toolchain (优化工具链)
- **职责**: 量化、蒸馏、vLLM 推理优化、性能对比
- **技术栈**: Python + FastAPI + Temporal
- **支持优化**:
  - GPTQ/AWQ 量化
  - 知识蒸馏
  - vLLM 高性能推理

### 4. RAG Engine (检索增强引擎)
- **职责**: 知识库管理、文档解析、向量化、语义检索
- **技术栈**: Python + LangChain + Milvus + PostgreSQL
- **核心功能**:
  - 多种文件格式解析
  - 智能分块策略
  - 混合检索 + 重排序

### 5. Evaluation Suite (评估套件)
- **职责**: 幻觉检测、毒性评估、忠实度计算、相关性评分
- **技术栈**: Python + FastAPI
- **评估指标**:
  - 幻觉率 (Hallucination Rate)
  - 毒性评分 (Toxicity Score)
  - 忠实度 (Faithfulness)
  - 相关性 (Relevance)

### 6. Multi-agent Orchestration (多智能体编排)
- **职责**: Workflow DAG 设计、任务调度、状态管理
- **技术栈**: Go + Temporal + PostgreSQL
- **节点类型**:
  - LLM 调用
  - 条件分支/循环
  - 知识库检索
  - 工具调用
  - 子工作流嵌套

### 7. Guardrails (安全护栏)
- **职责**: 输入/输出安全检查、敏感词过滤、PII 脱敏
- **技术栈**: Go + Redis + PostgreSQL

---

## 🔧 技术栈速查表

### 后端语言与框架
| 用途 | 技术 | 版本 |
|------|------|------|
| API 服务、业务逻辑 | Go | 1.22 |
| Web 框架 (Go) | Gin | 1.9 |
| ML 服务、评估、RAG | Python | 3.11 |
| Web 框架 (Python) | FastAPI | 0.109 |
| 工作流引擎 | Temporal | 1.22 |

### 数据库
| 用途 | 技术 | 版本 |
|------|------|------|
| 关系型数据 | PostgreSQL | 16 |
| 缓存、消息队列 | Redis | 7.2 |
| 向量检索 | Milvus | 2.3 |
| 对象存储 | MinIO | latest |

### 前端
| 用途 | 技术 | 版本 |
|------|------|------|
| UI 框架 | React | 18 |
| 类型系统 | TypeScript | 5 |
| 样式方案 | Tailwind CSS | v4 |
| 构建工具 | Vite | 5 |
| 服务端状态 | React Query | 5 |
| 客户端状态 | Zustand | 4 |
| Workflow 可视化 | React Flow | 11 |

### 基础设施
| 用途 | 技术 | 版本 |
|------|------|------|
| 容器编排 | Kubernetes | 1.29 |
| 包管理 | Helm | 3 |
| GitOps 部署 | Argo CD | 2.9 |
| 指标监控 | Prometheus | 2.49 |
| 可视化 | Grafana | 10.3 |

---

## 📊 数据库概览

### 核心表
- **users** - 用户表
- **model_versions** - 模型版本表
- **prompt_templates** - Prompt 模板表
- **prompt_versions** - Prompt 版本历史
- **knowledge_bases** - 知识库表
- **documents** - 文档表
- **chunks** - 文档分块表
- **workflows** - 工作流定义
- **workflow_runs** - 工作流执行记录
- **deployments** - 部署配置
- **evaluations** - 评估记录
- **api_keys** - API 密钥
- **audit_logs** - 审计日志

详见：`DATABASE-DESIGN.md`

---

## 🔌 API 概览

### 核心 API 组
| API 组 | 说明 |
|--------|------|
| `/api/v1/model-versions` | 模型版本管理 |
| `/api/v1/prompts` | Prompt 管理 |
| `/api/v1/knowledge-bases` | 知识库管理 |
| `/api/v1/workflows` | 工作流编排 |
| `/api/v1/deployments` | 部署管理 |
| `/api/v1/evaluations` | 评估监控 |
| `/api/v1/guardrails` | 安全护栏 |
| `/api/v1/optimizations` | 优化工具链 |

详见：`API-SPEC.md`

---

## 🚀 部署架构

### 环境划分
- **开发环境 (Dev)** - 日常开发测试
- **测试环境 (Test)** - QA 功能验证
- **预发环境 (Staging)** - 上线前验证
- **生产环境 (Production)** - 正式对外服务

### 扩缩容策略
- **API 服务**: 基于 CPU/内存使用率，自动扩缩容
- **Worker 服务**: 基于队列积压数，自动扩缩容
- **推理服务 (GPU)**: 基于排队请求数 + GPU 利用率

---

## 🔐 安全架构

### 认证体系
- JWT + Refresh Token (用户登录)
- OAuth 2.0 (第三方登录)
- API Key (服务间调用、开放 API)

### 授权模型
- RBAC (基于角色的访问控制)
- Owner → Admin → Editor → Viewer
- 细粒度权限：组织级 → 项目级 → 资源级

### 数据安全
- 传输加密：TLS 1.3
- 静态加密：数据库 TDE + 对象存储加密
- 应用层加密：AES-256-GCM 敏感字段
- 数据脱敏：日志、导出自动脱敏

---

## 📈 可观测性

### 三支柱体系

1. **Metrics (指标)** - Prometheus + Grafana
   - RED 方法：Rate / Errors / Duration
   - USE 方法：Utilization / Saturation / Errors

2. **Logging (日志)** - Loki + Grafana
   - 结构化 JSON 日志
   - 统一 trace_id 串联
   - 日志级别：debug / info / warn / error

3. **Tracing (追踪)** - OpenTelemetry + Jaeger
   - 全链路分布式追踪
   - 跨服务可见性
   - 性能瓶颈分析

---

## 📅 演进路线图

### MVP 阶段 (当前)
- ✅ 核心模型版本管理
- ✅ Prompt 编辑器与版本化
- ✅ 基础 RAG 检索
- ✅ 核心质量评估（幻觉、毒性）
- ✅ Web 控制台 v1

### Beta 阶段 (3 个月后)
- ✅ 多 Agent 编排引擎
- ✅ 优化工具链集成（量化、蒸馏、vLLM）
- ✅ GitHub CI/CD 集成
- ✅ 模型部署管理
- ✅ 增强的评估监控

### GA 阶段 (6 个月后)
- ✅ 团队协作与权限管理
- ✅ 高级 A/B 测试
- ✅ 成本分析与优化建议
- ✅ 企业级 SSO
- ✅ 多区域高可用部署

---

## 📚 文档导航

| 文档 | 推荐阅读顺序 |
|------|-------------|
| 1. ARCHITECTURE.md | ⭐⭐⭐⭐⭐ 首先阅读整体架构 |
| 2. TECH-STACK.md | ⭐⭐⭐⭐ 了解技术选型理由 |
| 3. DATABASE-DESIGN.md | ⭐⭐⭐ 查看数据模型设计 |
| 4. API-SPEC.md | ⭐⭐⭐ 查看接口详细规范 |

---

**文档版本**: v1.0  
**最后更新**: 2026-05-12  
**维护者**: Charlie (后端架构师)
