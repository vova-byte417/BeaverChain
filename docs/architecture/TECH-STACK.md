# BeaverChain 技术选型说明文档

**文档版本**: v1.0  
**创建日期**: 2026-05-12  
**架构师**: Charlie

---

## 1. 技术栈总览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                      │
│  React 18 + TypeScript 5 + Tailwind CSS v4 + Vite 5         │
│  React Query / Zustand / React Flow / Lucide Icons           │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                      API 网关层 (API Gateway)                 │
│  Nginx / Kong + mTLS + JWT Auth + Rate Limiting             │
└──────────────────────────────┬──────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼───────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  Model        │    │  Prompt Engine  │    │  Workflow       │
│  Registry     │    │                 │    │  Orchestration  │
│  Go + Gin     │    │  Go + Gin       │    │  Go + Temporal  │
└───────┬───────┘    └────────┬────────┘    └────────┬────────┘
        │                      │                      │
┌───────▼───────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  Evaluation   │    │  RAG Engine     │    │  Guardrails     │
│  Suite        │    │                 │    │                 │
│  Python +     │    │  Python +       │    │  Go + Redis     │
│  FastAPI      │    │  LangChain      │    │                 │
└───────┬───────┘    └────────┬────────┘    └────────┬────────┘
        │                      │                      │
┌───────▼──────────────────────▼──────────────────────▼────────┐
│                        数据层 (Data Layer)                      │
│  PostgreSQL 16 + Redis 7.2 + Milvus 2.3 + MinIO               │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                     基础设施 (Infrastructure)                 │
│  Kubernetes 1.29 + Helm + Argo CD + Istio + Prometheus       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 后端技术选型详解

### 2.1 Go + Gin (主要 API 服务)

**选用原因**

| 维度 | 说明 |
|------|------|
| **性能** | 编译型语言，原生协程，高并发场景表现优秀 |
| **开发效率** | 语法简洁，标准库丰富，Gin 框架生态成熟 |
| **部署简单** | 单二进制文件，无依赖，容器镜像小 |
| **类型安全** | 静态类型，编译期检查，减少运行时错误 |
| **团队技能** | 后端团队 Go 语言熟练度高 |

**适用服务**
- Model Registry（模型版本管理）
- Prompt Engine（提示词引擎）
- Guardrails（安全护栏）
- API Gateway（网关服务）
- Deployment Manager（部署管理）

**版本要求**
- Go: 1.22
- Gin: 1.9.x

### 2.2 Python + FastAPI (ML 相关服务)

**选用原因**

| 维度 | 说明 |
|------|------|
| **ML 生态** | PyTorch/TensorFlow/HuggingFace 等都是 Python 优先 |
| **数据处理** | Pandas/NumPy 等数据处理库非常成熟 |
| **开发速度** | 动态语言，原型迭代快，适合算法实验 |
| **LangChain** | 大模型应用开发的事实标准，Python 原生支持 |
| **FastAPI** | 高性能、自动生成 OpenAPI 文档、类型安全 |

**适用服务**
- Evaluation Suite（评估套件）
- RAG Engine（检索增强引擎）
- Optimization Toolchain（优化工具链）

**版本要求**
- Python: 3.11
- FastAPI: 0.109.x
- LangChain: 0.1.x

### 2.3 Temporal (工作流引擎)

**选用原因**

| 维度 | 说明 |
|------|------|
| **可靠执行** | 状态持久化，自动重试，支持长时间运行的工作流 |
| **可视化** | 内置 UI 可查看工作流执行状态和历史 |
| **多语言 SDK** | Go/Python/Java/TypeScript 都有官方 SDK |
| **定时器** | 原生支持定时任务、延迟执行、超时控制 |
| **可观测性** | 内置 metrics、tracing、logging |

**适用场景**
- 多 Agent 编排工作流
- 模型优化任务（量化、蒸馏）
- 批量评估任务
- 部署流水线

**版本要求**
- Temporal Server: 1.22.x
- Temporal Go SDK: 1.25.x
- Temporal Python SDK: 1.44.x

---

## 3. 数据库技术选型详解

### 3.1 PostgreSQL 16 (关系型数据库)

**选用原因**

| 特性 | 说明 |
|------|------|
| **JSONB 支持** | 存储半结构化数据，支持索引和查询 |
| **数组类型** | 原生支持数组，适合标签、多值属性 |
| **事务完整性** | ACID 兼容，支持复杂事务 |
| **扩展性** | 丰富的扩展（uuid-ossp, pg_trgm, vector 等） |
| **成熟稳定** | 经过数十年生产验证，社区活跃 |
| **高可用** | Streaming Replication + Patroni 方案成熟 |

**核心表使用场景**
- 模型版本元数据
- Prompt 模板和版本
- 用户与权限
- 工作流定义
- 部署配置
- 审计日志

**关键配置优化**
```ini
# 连接池
max_connections = 200
shared_buffers = 8GB
effective_cache_size = 24GB

# 写入优化
wal_buffers = 16MB
min_wal_size = 2GB
max_wal_size = 8GB

# 查询优化
work_mem = 64MB
maintenance_work_mem = 2GB
```

### 3.2 Redis 7.2 (缓存与消息队列)

**选用原因**

| 特性 | 说明 |
|------|------|
| **高性能** | 内存数据库，微秒级响应 |
| **丰富数据结构** | String/Hash/List/Set/ZSet/Stream/Geo |
| **持久化** | RDB + AOF 组合，数据安全 |
| **高可用** | Sentinel 哨兵 + Cluster 集群 |
| **Stream 消息队列** | 支持消费者组、ACK、消息持久化 |

**使用场景**
- API 响应缓存（模型版本、Prompt）
- 会话存储（用户 Session）
- 分布式锁
- 任务队列（Stream 结构）
- 限流计数器
- 实时指标聚合

**数据结构选型**
```
String: KV 缓存、计数器
Hash: 对象字段存储
List: 简单队列
Set: 去重集合
ZSet: 排行榜、有序集合
Stream: 任务队列、消费者组
```

### 3.3 Milvus 2.3 (向量数据库)

**选用原因**

| 特性 | 说明 |
|------|------|
| **专为向量优化** | 从底层设计用于向量相似度检索 |
| **多种索引算法** | HNSW/IVF_FLAT/IVF_SQ8 等 |
| **云原生** | Kubernetes 原生部署，弹性伸缩 |
| **高性能** | 支持十亿级向量毫秒级检索 |
| **过滤支持** | 向量检索 + 属性过滤组合查询 |

**使用场景**
- RAG 知识库向量存储与检索
- 语义相似度匹配
- 推荐系统召回层

**索引配置**
```python
# HNSW 索引配置 (平衡性能与精度)
index_params = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {
        "M": 16,              # 每层邻居数
        "efConstruction": 256 # 构建时探索邻居数
    }
}

# 查询参数
search_params = {
    "metric_type": "COSINE",
    "params": {"ef": 64}    # 查询时探索邻居数
}
```

### 3.4 MinIO (对象存储)

**选用原因**

| 特性 | 说明 |
|------|------|
| **S3 兼容** | API 完全兼容 AWS S3，无缝迁移 |
| **轻量级** | 单二进制文件，资源占用低 |
| **高性能** | 专为高性能读写优化 |
| **分布式** | 支持多节点分布式部署 |
| **生命周期管理** | 自动分层、过期删除 |

**存储内容**
- 模型权重文件
- 文档和知识库源文件
- 导出的评估报告
- 备份文件
- 日志归档

---

## 4. 前端技术选型详解

### 4.1 核心框架

**React 18**
- 理由：生态最成熟，团队熟悉度高
- 特性：并发特性、自动批处理、Suspense

**TypeScript 5**
- 理由：类型安全、IDE 支持好、减少运行时错误
- 特性：装饰器、const 类型参数

### 4.2 样式方案

**Tailwind CSS v4**
- 理由：原子化 CSS，开发效率高，一致的设计系统
- 特性：零配置、CSS 变量、浏览器原生、性能更优

**关键配置**
```javascript
// tailwind.config.js
export default {
  theme: {
    colors: {
      // Linear 风格深色主题
      canvas: '#010102',
      surface: '#0f1011',
      primary: '#5e6ad2',
      // ...
    }
  }
}
```

### 4.3 状态管理

**React Query (TanStack Query)**
- 服务端状态管理：缓存、重试、后台刷新、乐观更新
- 自动垃圾回收、重复请求去重
- DevTools 支持

**Zustand**
- 客户端全局状态：轻量、简单、TS 友好
- 无 Provider 嵌套地狱

### 4.4 关键库

| 库 | 用途 | 版本 |
|----|------|------|
| **React Flow** | Workflow 可视化编排 | 11.x |
| **TanStack Table** | 数据表格 | 8.x |
| **Zod** | 表单验证 | 3.x |
| **Lucide React** | 图标库 | latest |
| **Recharts** | 图表可视化 | 2.x |
| **Day.js** | 日期处理 | latest |

### 4.5 构建工具

**Vite 5**
- 理由：启动快、热更新快、ESM 原生、配置简单
- 特性：
  - 依赖预构建（esbuild）
  - 闪电般的 HMR
  - Rollup 生产构建
  - TypeScript 开箱即用

---

## 5. 基础设施选型详解

### 5.1 Kubernetes 1.29

**选用原因**
- 容器编排事实标准
- 自动扩缩容、滚动更新、自愈能力
- 服务发现、负载均衡
- 存储编排、配置管理
- 丰富的生态（Operator、CRD）

**核心组件**
- **Ingress Nginx**: 入口流量管理
- **CoreDNS**: 集群内 DNS
- **Metrics Server**: 资源指标收集
- **Cert Manager**: 证书自动管理

### 5.2 Helm 3

- 包管理工具，应用模板化
- 版本化部署、一键回滚
- values.yaml 环境配置分离

### 5.3 Argo CD

- GitOps 持续部署
- 声明式配置、自动化同步
- 可视化 UI、多集群支持

### 5.4 Istio (可选，企业版)

- 服务网格，流量治理
- mTLS 服务间认证
- 金丝雀发布、熔断、重试
- 可观测性（metrics/tracing/logging）

---

## 6. 可观测性技术栈

### 6.1 Metrics - Prometheus + Grafana

```
应用 → 埋点 (Prometheus Client)
    ↓
Prometheus → 拉取指标
    ↓
Grafana → 可视化仪表盘 + 告警规则
    ↓
Alertmanager → 通知（飞书/邮件/短信）
```

**核心指标**
- RED 方法：Rate（请求速率）、Errors（错误率）、Duration（延迟）
- USE 方法：Utilization（使用率）、Saturation（饱和度）、Errors（错误）

### 6.2 Logging - Loki + Grafana

```
应用日志 → 结构化 JSON
    ↓
Vector/FluentBit → 采集、过滤、转发
    ↓
Loki → 索引、存储、查询
    ↓
Grafana → 日志查询界面
```

**日志规范**
```json
{
  "timestamp": "2026-05-12T10:30:00Z",
  "level": "info",
  "service": "model-registry",
  "trace_id": "abc123xyz",
  "span_id": "def456",
  "user_id": "user_789",
  "message": "Model version created",
  "data": {"version_id": "mv_123"}
}
```

### 6.3 Tracing - OpenTelemetry

- 全链路追踪，跨服务可见
- 自动埋点，少侵入
- 支持多种后端（Jaeger、Zipkin、OTLP）

---

## 7. 安全技术选型

### 7.1 认证授权

**JWT (JSON Web Token)**
- 无状态、跨域友好
- 短周期 Access Token + 长周期 Refresh Token

**OAuth 2.0**
- GitHub/Google 第三方登录
- 企业 SSO 支持（OIDC/SAML）

**API Key**
- 服务间调用
- 对外开放 API

### 7.2 数据加密

**传输加密**
- 强制 TLS 1.3，禁用旧版本
- 内部服务间 mTLS（Istio）

**静态加密**
- 数据库透明数据加密 (TDE)
- 对象存储服务端加密
- 敏感字段应用层加密 (AES-256-GCM)

### 7.3 漏洞扫描

- **Trivy**: 容器镜像漏洞扫描
- **Gosec**: Go 代码安全扫描
- **Bandit**: Python 代码安全扫描
- **OWASP ZAP**: Web 应用动态扫描

---

## 8. CI/CD 技术栈

```
代码提交 → GitHub Actions
    ↓
静态检查 (ESLint/GoLint)
    ↓
安全扫描 (Trivy/Gosec)
    ↓
单元测试 (Jest/GoTest)
    ↓
构建镜像 (Docker/BuildKit)
    ↓
推送到镜像仓库 (Harbor)
    ↓
Argo CD → 同步到 K8s 集群
    ↓
健康检查 → 完成
```

---

## 9. 技术选型对比分析

### 9.1 Go vs Python 取舍

| 场景 | Go | Python | 推荐 |
|------|----|--------|------|
| **高并发 API** | ✅ 优秀 | ⚠️ 一般 | Go |
| **ML 模型推理** | ⚠️ 生态弱 | ✅ 生态强 | Python |
| **数据处理** | ⚠️ 库少 | ✅ Pandas/Numpy | Python |
| **微服务业务逻辑** | ✅ 强类型、性能好 | ⚠️ 动态类型 | Go |
| **快速原型开发** | ⚠️ 编译慢 | ✅ 快速迭代 | Python |

**结论：混合架构，各擅其长**

### 9.2 Milvus vs pgvector 对比

| 维度 | Milvus | pgvector |
|------|--------|----------|
| **向量规模** | 十亿级 | 百万级 |
| **查询延迟** | < 10ms | < 50ms |
| **索引算法** | HNSW/IVF/Annoy | HNSW/IVFFlat |
| **过滤支持** | ✅ 标量过滤组合 | ⚠️ 需要二次过滤 |
| **运维复杂度** | 较高（分布式） | 低（PostgreSQL 扩展） |
| **适用场景** | RAG 知识库、大规模 | 小规模、简单场景 |

**结论：RAG 引擎用 Milvus，简单向量场景可用 pgvector**

### 9.3 Redis Stream vs Kafka 对比

| 维度 | Redis Stream | Kafka |
|------|-------------|-------|
| **吞吐量** | 万级 QPS | 百万级 QPS |
| **延迟** | 亚毫秒 | 毫秒级 |
| **运维复杂度** | 低 | 高 |
| **消息保留** | 可配置但有限 | 长期、大容量 |
| **消费者模式** | 消费者组 | 消费者组 + 分区 |
| **适用场景** | 任务队列、实时消息 | 日志、数据流、事件溯源 |

**结论：任务队列用 Redis Stream，日志流用 Kafka**

---

## 10. 技术演进路线图

### 10.1 MVP 阶段 (当前)

- ✅ PostgreSQL 单主 + 只读副本
- ✅ Redis 主从 + Sentinel
- ✅ Milvus 单机版（后续升级集群）
- ✅ MinIO 单节点（后续升级分布式）

### 10.2 Beta 阶段 (3 个月后)

- ⏳ PostgreSQL 分片（按用户 ID）
- ⏳ Redis Cluster 集群化
- ⏳ Milvus 分布式集群
- ⏳ MinIO 多节点分布式部署
- ⏳ Istio 服务网格接入

### 10.3 GA 阶段 (6 个月后)

- ⏳ 多区域部署
- ⏳ 异地容灾
- ⏳ 自动故障转移
- ⏳ 完整的混沌工程能力

---

## 11. 技术债务管理

### 11.1 需重构清单

| 模块 | 债务类型 | 优先级 | 计划时间 |
|------|---------|--------|---------|
| 鉴权中间件 | 代码重复 | 高 | MVP 后 |
| 配置管理 | 硬编码 | 中 | Beta 前 |
| 错误处理 | 不一致 | 中 | Beta 前 |
| 日志规范 | 格式不统一 | 低 | GA 前 |

### 11.2 重构策略

- 每月第一个周五：重构日
- 技术债务清零原则：不欠账上线
- 新功能开发时间的 20% 用于偿还债务

---

**文档结束**
