# BeaverChain 系统架构设计文档

**文档版本**: v1.0  
**创建日期**: 2026-05-12  
**架构师**: Charlie

---

## 1. 架构总览

### 1.1 设计原则

1. **模块化设计** - 各功能模块松耦合，支持独立扩展和部署
2. **API 优先** - 所有功能通过 REST API 暴露，支持多端接入
3. **高可用性** - 无状态服务设计，支持水平扩展
4. **数据一致性** - 关键操作使用事务，保证数据完整性
5. **可观测性** - 统一的日志、监控、追踪体系

### 1.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         客户端层 (Client Layer)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Web 控制台  │  │  Python SDK  │  │  JS/TS SDK   │  │ CLI 工具  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API 网关层 (API Gateway)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  认证    │  │  限流    │  │  日志    │  │  路由    │  │  协议  │ │
│  │  授权    │  │  熔断    │  │  审计    │  │          │  │  转换  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      微服务层 (Microservices)                         │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Model Registry  │  │  Prompt Engine   │  │  Optimization    │  │
│  │  (模型版本化)    │  │  (提示词引擎)    │  │  Toolchain       │  │
│  │                  │  │                  │  │  (优化工具链)    │  │
│  │  · Go + Gin      │  │  · Go + Gin      │  │  · Python        │  │
│  │  · PostgreSQL    │  │  · PostgreSQL    │  │  · FastAPI       │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  RAG Engine      │  │  Evaluation      │  │  Multi-agent     │  │
│  │  (检索增强)      │  │  Suite           │  │  Orchestration   │  │
│  │                  │  │  (评估套件)      │  │  (多智能体编排)  │  │
│  │  · Python        │  │  · Python        │  │  · Go + Python   │  │
│  │  · FastAPI       │  │  · FastAPI       │  │  · Temporal      │  │
│  │  · Milvus        │  │  · Redis         │  │  · PostgreSQL    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐                           │
│  │  Monitoring      │  │  Guardrails      │                           │
│  │  (监控模块)      │  │  (安全护栏)      │                           │
│  │                  │  │                  │                           │
│  │  · Prometheus    │  │  · Go + Gin      │                           │
│  │  · Grafana       │  │  · Redis         │                           │
│  │  · Alertmanager  │  │  · PostgreSQL    │                           │
│  └──────────────────┘  └──────────────────┘                           │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        数据层 (Data Layer)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  PostgreSQL  │  │    Redis     │  │    Milvus    │  │  S3/OSS  │ │
│  │  (元数据)    │  │  (缓存/队列) │  │  (向量存储)  │  │  (文件)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      基础设施层 (Infrastructure)                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Kubernetes 集群                             │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │  │
│  │  │ API Pod │  │Workflow │  │ vLLM    │  │ Worker  │         │  │
│  │  │ (HPA)   │  │ Pod     │  │ GPU Pod │  │ Pod     │         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Argo CD     │  │   Istio      │  │ cert-manager │               │
│  │  (部署)      │  │ (服务网格)   │  │  (证书管理)   │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 技术选型说明

### 2.1 后端技术栈

| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|---------|
| **Go** | 1.22 | API 服务开发 | 高性能、并发友好、编译型语言、部署简单 |
| **Gin** | 1.9 | HTTP 框架 | 轻量、高性能、生态成熟、中间件支持完善 |
| **Python** | 3.11 | ML 相关服务 | ML 生态最完善、数据处理能力强、团队熟悉 |
| **FastAPI** | 0.109 | Python API 框架 | 自动生成 OpenAPI 文档、类型安全、异步支持 |
| **gRPC** | 1.60 | 服务间通信 | 高性能、强类型、支持流式通信 |
| **Temporal** | 1.22 | 工作流引擎 | 可靠的工作流编排、状态持久化、重试机制 |

### 2.2 数据库与存储

| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|---------|
| **PostgreSQL** | 16 | 关系型数据库 | 成熟稳定、支持 JSONB、事务完善、生态丰富 |
| **Redis** | 7.2 | 缓存、消息队列 | 高性能、支持多种数据结构、Pub/Sub、Stream |
| **Milvus** | 2.3 | 向量数据库 | 专为向量检索优化、支持 ANN 算法、云原生 |
| **MinIO** | latest | 对象存储 | S3 兼容、高性能、轻量级、开源 |

### 2.3 基础设施

| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|---------|
| **Kubernetes** | 1.29 | 容器编排 | 云原生标准、自动扩缩容、滚动更新、服务发现 |
| **Helm** | 3.14 | 包管理 | K8s 应用部署标准、模板化、版本管理 |
| **Prometheus** | 2.49 | 监控指标 | CNCF 毕业项目、生态完善、告警能力强 |
| **Grafana** | 10.3 | 可视化面板 | 图表丰富、数据源多、告警集成好 |
| **Istio** | 1.20 | 服务网格 | 流量管理、安全、可观测性 |

---

## 3. 核心模块详细设计

### 3.1 Model Registry (模型版本化模块)

#### 3.1.1 模块职责
- 模型版本的 CRUD 操作
- 版本快照与回滚
- 版本对比与差异计算
- Lineage 血缘追踪
- 模型元数据管理

#### 3.1.2 接口设计

```
POST   /api/v1/model-versions              # 创建模型版本
GET    /api/v1/model-versions              # 获取版本列表
GET    /api/v1/model-versions/:id          # 获取版本详情
PUT    /api/v1/model-versions/:id          # 更新版本信息
DELETE /api/v1/model-versions/:id          # 删除版本
POST   /api/v1/model-versions/:id/rollback # 回滚到指定版本
GET    /api/v1/model-versions/compare      # 对比两个版本
GET    /api/v1/model-versions/:id/lineage  # 获取版本血缘
```

#### 3.1.3 核心数据结构

```go
type ModelVersion struct {
    ID          uuid.UUID      `json:"id"`
    Name        string         `json:"name"`
    Version     string         `json:"version"` // semver
    Description string         `json:"description"`
    Status      VersionStatus  `json:"status"`  // draft/testing/production/archived
    OwnerID     uuid.UUID      `json:"owner_id"`
    Tags        []string       `json:"tags"`
    
    // 组件配置
    WeightsConfig    WeightsConfig    `json:"weights_config"`
    PromptConfig     PromptConfig     `json:"prompt_config"`
    RAGConfig        RAGConfig        `json:"rag_config"`
    GuardrailsConfig GuardrailsConfig `json:"guardrails_config"`
    InferenceParams  InferenceParams  `json:"inference_params"`
    
    // 元数据
    Lineage        LineageInfo     `json:"lineage"`
    EvaluationMetrics EvaluationMetrics `json:"evaluation_metrics"`
    CreatedAt      time.Time       `json:"created_at"`
    UpdatedAt      time.Time       `json:"updated_at"`
}

type WeightsConfig struct {
    ModelType     string            `json:"model_type"` // gpt4, claude, llama, custom
    Provider      string            `json:"provider"`
    ModelID       string            `json:"model_id"`
    BaseURL       string            `json:"base_url,omitempty"`
    APIKeySecret  string            `json:"api_key_secret"`
    Parameters    map[string]any    `json:"parameters"`
}

type LineageInfo struct {
    ParentVersionID *uuid.UUID        `json:"parent_version_id"`
    ForkedFrom      *uuid.UUID        `json:"forked_from"`
    DerivedFrom     []DerivedFromItem `json:"derived_from"`
    CreatedBy       uuid.UUID         `json:"created_by"`
}
```

---

### 3.2 Prompt Engine (提示词引擎模块)

#### 3.2.1 模块职责
- Prompt 的版本化管理
- 富文本编辑器支持
- 变量解析与模板渲染
- 分支管理与合并
- Prompt 测试与效果对比

#### 3.2.2 核心功能流程

```
用户创建 Prompt
    ↓
编辑器编写内容（变量高亮 {{var}}）
    ↓
点击预览/测试
    ↓
模板解析 + 变量填充
    ↓
调用 LLM 获取结果
    ↓
展示对比（原始 Prompt → 渲染后 → LLM 输出）
    ↓
满意后提交 → 创建新版本
```

#### 3.2.3 数据结构

```go
type Prompt struct {
    ID          uuid.UUID  `json:"id"`
    Name        string     `json:"name"`
    Description string     `json:"description"`
    Content     string     `json:"content"` // 支持 {{variable}} 语法
    Variables   []Variable `json:"variables"`
    
    // 版本控制
    CurrentVersionID uuid.UUID   `json:"current_version_id"`
    Branches         []BranchInfo `json:"branches"`
    
    // 元数据
    OwnerID    uuid.UUID `json:"owner_id"`
    ModelVersionID *uuid.UUID `json:"model_version_id,omitempty"`
    Tags       []string  `json:"tags"`
    CreatedAt  time.Time `json:"created_at"`
    UpdatedAt  time.Time `json:"updated_at"`
}

type Variable struct {
    Name        string `json:"name"`
    Type        string `json:"type"` // string, number, boolean, array, object
    Description string `json:"description"`
    DefaultValue any    `json:"default_value,omitempty"`
    Required    bool   `json:"required"`
}

type PromptVersion struct {
    ID        uuid.UUID `json:"id"`
    PromptID  uuid.UUID `json:"prompt_id"`
    Version   string    `json:"version"`
    Content   string    `json:"content"`
    CommitMsg string    `json:"commit_msg"`
    CreatedBy uuid.UUID `json:"created_by"`
    CreatedAt time.Time `json:"created_at"`
}
```

---

### 3.3 Optimization Toolchain (优化工具链模块)

#### 3.3.1 模块职责
- 量化工具集成 (GPTQ/AWQ)
- 知识蒸馏配置与执行
- vLLM 推理优化
- DeepSpeed 训练优化
- 优化前后性能对比

#### 3.3.2 优化任务流程

```
用户选择优化类型
    ↓
配置优化参数
    ↓
验证配置合法性
    ↓
创建优化任务（状态: pending）
    ↓
Worker 拾取任务 → running
    ↓
执行优化（量化/蒸馏/...）
    ↓
记录中间结果
    ↓
完成 → success/failed
    ↓
生成性能对比报告
```

#### 3.3.3 支持的优化类型

| 优化类型 | 描述 | 适用场景 |
|---------|------|---------|
| **GPTQ 量化** | 4-bit/8-bit 权重量化 | 降低显存占用，加速推理 |
| **AWQ 量化** | Activation-aware 量化 | 精度损失更小，显存更优 |
| **知识蒸馏** | 大模型 → 小模型蒸馏 | 轻量化部署，成本优化 |
| **vLLM** | PagedAttention 推理 | 高吞吐量推理服务 |
| **DeepSpeed** | 分布式训练优化 | 大规模模型训练加速 |

---

### 3.4 RAG Engine (检索增强模块)

#### 3.4.1 模块职责
- 知识库管理
- 文档解析与向量化
- 向量检索
- 检索策略配置
- 检索结果重排序

#### 3.4.2 检索流程

```
用户查询
    ↓
Query 重写（可选）
    ↓
向量化（Embedding 模型）
    ↓
向量检索（Milvus）
    ↓
粗排 → 候选集
    ↓
精排（Reranker 模型）
    ↓
最终检索结果
    ↓
注入 Prompt 上下文
```

#### 3.4.3 配置参数

```go
type RAGConfig struct {
    KnowledgeBaseID uuid.UUID `json:"knowledge_base_id"`
    
    // 检索配置
    TopK            int     `json:"top_k"`            // 返回结果数
    ScoreThreshold  float64 `json:"score_threshold"`  // 相似度阈值
    SearchStrategy  string  `json:"search_strategy"`  // hybrid, dense, sparse
    
    // 向量化配置
    EmbeddingModel  ModelRef `json:"embedding_model"`
    ChunkSize       int      `json:"chunk_size"`       // 分块大小
    ChunkOverlap    int      `json:"chunk_overlap"`    // 重叠大小
    
    // 重排序配置
    EnableRerank   bool     `json:"enable_rerank"`
    RerankModel    ModelRef `json:"rerank_model,omitempty"`
    RerankTopN     int      `json:"rerank_top_n"`
    
    // 高级选项
    EnableHybridSearch   bool `json:"enable_hybrid_search"`
    EnableQueryExpansion bool `json:"enable_query_expansion"`
}
```

---

### 3.5 Evaluation Suite (评估套件模块)

#### 3.5.1 模块职责
- 幻觉率检测
- 毒性评分
- 回答忠实度计算
- 相关性评估
- 质量指标聚合
- 评估报告生成

#### 3.5.2 核心评估指标

| 指标 | 计算方法 | 目标值 | 说明 |
|------|---------|-------|------|
| **幻觉率** | 含幻觉输出 / 总输出 | < 5% | 检测与事实不符的内容 |
| **毒性评分** | Perspective API + 本地分类器 | < 0.1 | 检测有害、冒犯性内容 |
| **忠实度** | 回答与上下文的语义对齐度 | > 90% | 衡量回答是否基于上下文 |
| **相关性** | 回答与问题的相关程度 | > 95% | 衡量是否答非所问 |
| **Bleu/Rouge** | 与参考答案的重叠度 | > 0.7 | 文本生成质量指标 |
| **延迟** | P50/P95/P99 响应时间 | < 500ms (P95) | 性能指标 |

#### 3.5.3 幻觉检测流程

```
待检测回答 + 上下文
    ↓
分事实句
    ↓
逐句验证
    ↓
基于 Embedding 相似度
基于 NLI（自然语言推理）
基于 LLM 自我验证
    ↓
综合评分
    ↓
输出幻觉率 + 问题片段高亮
```

---

### 3.6 Multi-agent Orchestration (多智能体编排模块)

#### 3.6.1 模块职责
- Workflow 可视化设计
- 工作流执行引擎
- 任务调度与状态管理
- Lineage 数据收集
- 子工作流嵌套支持

#### 3.6.2 节点类型

| 节点类型 | 描述 | 配置项 |
|---------|------|-------|
| **LLM 调用** | 调用大模型推理 | 模型版本、Prompt 模板、参数 |
| **条件分支** | if/else 逻辑 | 条件表达式、分支配置 |
| **循环** | for/while 循环 | 循环条件、最大迭代次数 |
| **数据处理** | 转换数据格式 | 转换表达式、JQ 脚本 |
| **工具调用** | 调用外部工具 | 工具类型、参数映射 |
| **知识库检索** | RAG 检索 | 检索配置、TopK |
| **子工作流** | 嵌套调用 | Workflow ID、参数映射 |
| **并行分支** | 并行执行 | 分支列表、聚合策略 |

#### 3.6.3 执行状态机

```
PENDING → SCHEDULED → RUNNING → SUCCESS
                        ↓        ↓
                    PAUSED    FAILED
                        ↓
                    CANCELLED
```

---

### 3.7 Monitoring (监控模块)

#### 3.7.1 模块职责
- 系统指标采集
- 业务指标监控
- 告警规则管理
- 告警通知推送
- 监控仪表盘

#### 3.7.2 核心监控指标

**系统指标**
- API 吞吐量（QPS）
- 响应时间 P50/P95/P99
- 错误率
- 服务可用性
- 资源利用率（CPU/内存/GPU）

**业务指标**
- 模型调用次数
- Token 消耗量
- 平均每次调用成本
- 版本创建频率
- Workflow 执行成功率

**质量指标**
- 幻觉率趋势
- 毒性评分趋势
- 忠实度评分趋势
- 用户满意度评分

---

### 3.8 Guardrails (安全护栏模块)

#### 3.8.1 模块职责
- 输入内容安全检查
- 输出内容安全检查
- 敏感词过滤
- 幻觉检测
- 内容策略配置
- 实时规则更新

#### 3.8.2 检查流程

```
用户输入
    ↓
前置检查
    ├─ 敏感词过滤
    ├─ 注入攻击检测
    └─ 越权请求检测
    ↓
模型处理
    ↓
后置检查
    ├─ 幻觉检测
    ├─ 毒性评分
    ├─ 事实一致性
    └─ PII 信息脱敏
    ↓
最终输出
```

---

## 4. 数据库设计

### 4.1 ER 图概览

```
┌─────────────────┐
│   users         │
├─────────────────┤
│ id (PK)         │
│ email           │
│ name            │
│ password_hash   │
│ role            │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐         ┌─────────────────┐
│ model_versions  │         │ prompt_templates│
├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ id (PK)         │
│ name            │         │ name            │
│ version         │         │ content         │
│ status          │         │ version         │
│ owner_id (FK)   │         │ model_version_id│
│ weights_config  │         │ owner_id        │
│ prompt_config   │         └─────────────────┘
│ rag_config      │
│ guardrails_cfg  │                   │
│ tags            │                   │ 1:N
│ created_at      │                   ▼
│ updated_at      │         ┌─────────────────┐
└────────┬────────┘         │ prompt_versions │
         │                  ├─────────────────┤
         │ 1:N              │ id (PK)         │
         ▼                  │ prompt_id (FK)  │
┌─────────────────┐         │ version         │
│ deployments     │         │ content         │
├─────────────────┤         │ commit_msg      │
│ id (PK)         │         │ created_by      │
│ model_version_id│         │ created_at      │
│ environment     │         └─────────────────┘
│ status          │
│ traffic_weight  │
└─────────────────┘

┌─────────────────┐
│ workflows       │
├─────────────────┤
│ id (PK)         │
│ name            │
│ definition (JSON)│
│ version         │
│ owner_id        │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│ workflow_runs   │
├─────────────────┤
│ id (PK)         │
│ workflow_id (FK)│
│ status          │
│ input_data      │
│ output_data     │
│ started_at      │
│ finished_at     │
└─────────────────┘
```

### 4.2 核心表结构

详见 `DATABASE-DESIGN.md` 文档

---

## 5. API 设计规范

### 5.1 RESTful API 规范

#### URL 设计
- 使用名词复数形式：`/api/v1/model-versions`
- 层级关系清晰：`/api/v1/models/{id}/versions`
- 查询参数用于过滤、排序、分页
- 版本号在 URL 路径中

#### HTTP 方法语义
```
GET    /resource          # 获取列表
GET    /resource/:id      # 获取单个
POST   /resource          # 创建
PUT    /resource/:id      # 全量更新
PATCH  /resource/:id      # 部分更新
DELETE /resource/:id      # 删除
```

#### 统一响应格式

**成功响应**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "example"
  },
  "request_id": "req_abc123",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

**错误响应**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "版本号格式错误",
    "details": [
      { "field": "version", "reason": "必须符合 semver 格式" }
    ]
  },
  "request_id": "req_abc123",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

#### 分页规范

**请求参数**
```
GET /api/v1/model-versions?page=1&page_size=20&sort=-created_at,name
```

**响应格式**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 156,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  },
  "request_id": "..."
}
```

### 5.2 服务间通信 - gRPC

使用 gRPC 进行服务间高性能通信，Protocol Buffers 定义接口。

**示例 proto 定义**
```protobuf
syntax = "proto3";

package version.v1;

service VersionService {
  rpc GetModelVersion(GetModelVersionRequest) returns (GetModelVersionResponse);
  rpc ListModelVersions(ListModelVersionsRequest) returns (ListModelVersionsResponse);
  rpc CreateModelVersion(CreateModelVersionRequest) returns (CreateModelVersionResponse);
  rpc RollbackModelVersion(RollbackModelVersionRequest) returns (RollbackModelVersionResponse);
}
```

---

## 6. 部署架构

### 6.1 Kubernetes 部署架构

```
                    ┌─────────────┐
                    │   Ingress   │
                    │ Controller  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Istio    │
                    │ ServiceMesh │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌────▼─────┐    ┌────▼─────┐
    │ API Pod   │   │Workflow   │    │ vLLM     │
    │ (HPA)     │   │Pod        │    │ GPU Pod  │
    └─────┬─────┘   └───────────┘    └─────┬─────┘
          │                                  │
    ┌─────▼─────┐                     ┌────▼─────┐
    │ PostgreSQL │                     │  Milvus  │
    │ (Primary)  │                     │ Cluster  │
    └─────┬─────┘                     └─────┬─────┘
          │                                  │
    ┌─────▼─────┐                     ┌────▼─────┐
    │ Redis     │                     │  MinIO   │
    │ Cluster   │                     │  Object  │
    └───────────┘                     │  Storage │
                                      └───────────┘
```

### 6.2 扩缩容策略

| 服务 | 扩缩容指标 | 目标值 |
|------|-----------|-------|
| **API Gateway** | CPU 使用率 | 70% |
| | 内存使用率 | 80% |
| **Model Registry** | 队列积压数 | 100 |
| **Workflow Engine** | 等待任务数 | 50 |
| **vLLM 推理** | GPU 利用率 | 80% |
| | 排队请求数 | 20 |

### 6.3 多环境部署

| 环境 | 用途 | 数据隔离 | 成本控制 |
|------|------|---------|---------|
| **开发环境** | 日常开发测试 | 独立数据库 | 低配资源 |
| **测试环境** | QA 功能测试 | 独立数据库 | 中等配置 |
| **预发环境** | 上线前验证 | 生产数据快照 | 生产配置 |
| **生产环境** | 正式对外服务 | 完整隔离 | 高可用配置 |

---

## 7. 安全架构

### 7.1 认证体系

```
用户认证
    ├─ Email + Password
    ├─ OAuth2 (GitHub/Google)
    ├─ SSO (SAML/OIDC)
    └─ API Key

服务间认证
    ├─ mTLS
    ├─ Service Account Token
    └─ SPIFFE/SPIRE (可选)
```

### 7.2 授权模型 - RBAC + ABAC

**角色层级**
```
Owner → Admin → Editor → Viewer → Guest
```

**权限粒度**
- 组织级权限
- 项目级权限
- 资源级权限（单个模型版本）
- 基于标签的权限
- 基于环境的权限

### 7.3 数据安全

**传输安全**
- 强制 TLS 1.3
- 内部服务间也启用 TLS
- 证书自动续期 (cert-manager)

**静态加密**
- 数据库透明数据加密 (TDE)
- 对象存储服务端加密
- 敏感字段应用层加密 (AES-256-GCM)

**数据脱敏**
- 日志中不输出敏感数据
- API 响应按需脱敏
- 导出数据自动脱敏

---

## 8. 可观测性架构

### 8.1 日志体系

```
应用日志 (结构化 JSON)
    ↓
Fluent Bit / Vector
    ↓
Loki / Elasticsearch
    ↓
Grafana 日志查询
```

**日志字段规范**
```json
{
  "timestamp": "ISO8601",
  "level": "info/debug/warn/error",
  "service": "model-registry",
  "trace_id": "abc123",
  "span_id": "def456",
  "user_id": "user_789",
  "message": "描述信息",
  "data": {}
}
```

### 8.2 追踪体系

OpenTelemetry 全链路追踪

```
用户请求 → API Gateway → Service A → Service B → DB
           ↓             ↓           ↓         ↓
       trace_id 贯穿整个调用链
```

### 8.3 告警分级

| 级别 | 响应时间 | 通知渠道 | 示例 |
|------|---------|---------|------|
| **P0 (Critical)** | 立即响应 (< 5分钟) | 电话 + 短信 + 群@ | 服务不可用、数据丢失 |
| **P1 (High)** | 1 小时内 | 群@ + 邮件 | 单个实例故障、错误率>5% |
| **P2 (Medium)** | 工作日 4 小时 | 邮件 | 内存使用率高、证书即将过期 |
| **P3 (Low)** | 下次迭代 | 工单系统 | 性能优化建议、小的体验问题 |

---

## 9. 扩展性设计

### 9.1 插件体系

支持第三方插件扩展：
- 自定义评估器
- 新的模型提供商
- 自定义优化工具
- 通知渠道集成
- 外部系统对接

### 9.2 Webhook 事件

系统关键事件支持 Webhook 推送：
- 模型版本创建/更新
- 部署状态变更
- 评估告警触发
- Workflow 执行完成
- 用户操作审计

---

## 10. 总结

本架构设计遵循以下核心理念：

1. **模块化、松耦合** - 每个微服务独立部署、独立扩展
2. **技术栈务实选择** - Go 做 API，Python 做 ML，各展所长
3. **云原生架构** - Kubernetes + 微服务 + DevOps 最佳实践
4. **企业级特性** - 完善的安全、监控、高可用方案
5. **可扩展性** - 预留插件体系、Webhook、API 接口

该架构能够支撑 BeaverChain 从 MVP 到大规模企业级应用的演进需求。

---

**文档结束**
