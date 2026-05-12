# BeaverChain 数据库设计文档

**文档版本**: v1.0  
**创建日期**: 2026-05-12  
**架构师**: Charlie

---

## 1. 数据库选型

### 1.1 多数据库策略

| 数据类型 | 数据库 | 版本 | 用途 |
|---------|--------|------|------|
| **业务元数据** | PostgreSQL | 16 | 关系型数据、事务支持 |
| **缓存/会话** | Redis | 7.2 | 高性能 KV、消息队列 |
| **向量数据** | Milvus | 2.3 | 向量相似度检索 |
| **大文件** | MinIO | latest | 对象存储（模型权重、文档） |
| **时序指标** | Prometheus | 2.49 | 监控指标 |
| **日志** | Loki | 3.0 | 日志存储与查询 |

### 1.2 PostgreSQL 配置

**关键配置**
- 字符集：UTF-8
- 时区：UTC
- 连接池：PgBouncer
- 高可用：Streaming Replication

**扩展启用**
- `uuid-ossp` - UUID 生成
- `pg_trgm` - 模糊搜索
- `btree_gin` - GIN 索引
- `vector` - pgvector（轻量级向量场景）

---

## 2. ER 图

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ email (UK)      │
│ name            │
│ password_hash   │
│ role            │
│ avatar_url      │
│ last_login_at   │
│ is_active       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1
         │
         │ N
         ▼
┌─────────────────┐         ┌─────────────────┐
│ model_versions  │         │ prompt_templates│
├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ id (PK)         │
│ name            │         │ name            │
│ version         │         │ description     │
│ description     │         │ content         │
│ status          │         │ variables (JSONB)│
│ owner_id (FK)   │         │ owner_id (FK)   │
│ weights (JSONB) │         │ model_version_id│
│ prompt (JSONB)  │         │ tags (ARRAY)    │
│ rag (JSONB)     │         │ created_at      │
│ guardrails(JSONB)│        │ updated_at      │
│ tags (ARRAY)    │         └─────────────────┘
│ created_at      │
│ updated_at      │                   │ 1
└────────┬────────┘                   │
         │ 1                           │ N
         │                             ▼
         │ N                  ┌─────────────────┐
         ▼                    │ prompt_versions │
┌─────────────────┐           ├─────────────────┤
│ deployments     │           │ id (PK)         │
├─────────────────┤           │ prompt_id (FK)  │
│ id (PK)         │           │ version         │
│ model_version_id│           │ content         │
│ environment     │           │ commit_msg      │
│ status          │           │ created_by (FK) │
│ traffic_weight  │           │ created_at      │
│ config (JSONB)  │           └─────────────────┘
│ created_at      │
│ updated_at      │
└─────────────────┘

┌─────────────────┐
│ knowledge_bases │
├─────────────────┤
│ id (PK)         │
│ name            │
│ description     │
│ owner_id (FK)   │
│ embedding_model │
│ chunk_size      │
│ chunk_overlap   │
│ vector_db       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1
         │
         │ N
         ▼
┌─────────────────┐
│ documents       │
├─────────────────┤
│ id (PK)         │
│ kb_id (FK)      │
│ title           │
│ file_path       │
│ file_size       │
│ mime_type       │
│ status          │
│ metadata (JSONB)│
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1
         │
         │ N
         ▼
┌─────────────────┐
│ chunks          │
├─────────────────┤
│ id (PK)         │
│ doc_id (FK)     │
│ kb_id (FK)      │
│ content         │
│ vector_id       │  ────> Milvus
│ embedding (JSON)│
│ metadata (JSONB)│
│ chunk_index     │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│ workflows       │
├─────────────────┤
│ id (PK)         │
│ name            │
│ description     │
│ owner_id (FK)   │
│ definition      │  ──> JSONB DAG 定义
│ version         │
│ is_active       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1
         │
         │ N
         ▼
┌─────────────────┐
│ workflow_runs   │
├─────────────────┤
│ id (PK)         │
│ workflow_id (FK)│
│ status          │
│ input (JSONB)   │
│ output (JSONB)  │
│ error           │
│ duration_ms     │
│ started_at      │
│ finished_at     │
└────────┬────────┘
         │ 1
         │
         │ N
         ▼
┌─────────────────┐
│ step_executions │
├─────────────────┤
│ id (PK)         │
│ run_id (FK)     │
│ node_id         │
│ node_type       │
│ status          │
│ input (JSONB)   │
│ output (JSONB)  │
│ error           │
│ duration_ms     │
│ started_at      │
│ finished_at     │
└─────────────────┘

┌─────────────────┐
│ evaluations     │
├─────────────────┤
│ id (PK)         │
│ model_version_id│
│ eval_type       │
│ status          │
│ metrics (JSONB) │
│ dataset_id      │
│ sample_size     │
│ failed_samples  │
│ started_at      │
│ finished_at     │
└─────────────────┘

┌─────────────────┐
│ api_keys        │
├─────────────────┤
│ id (PK)         │
│ name            │
│ key_hash        │
│ key_prefix      │
│ owner_id (FK)   │
│ permissions     │
│ rate_limit      │
│ last_used_at    │
│ expires_at      │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│ audit_logs      │
├─────────────────┤
│ id (PK)         │
│ action          │
│ resource_type   │
│ resource_id     │
│ user_id (FK)    │
│ ip_address      │
│ user_agent      │
│ changes (JSONB) │
│ created_at      │
└─────────────────┘
```

---

## 3. 表结构定义 (PostgreSQL)

### 3.1 用户与权限

#### users 表

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'owner', 'editor', 'viewer', 'user')),
    avatar_url VARCHAR(500),
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
```

#### api_keys 表

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permissions JSONB DEFAULT '["read", "write"]',
    rate_limit INTEGER DEFAULT 1000,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_keys_owner ON api_keys(owner_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);
```

---

### 3.2 模型版本管理

#### model_versions 表

```sql
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'testing', 'staging', 'production', 'archived')),
    owner_id UUID NOT NULL REFERENCES users(id),
    project_id UUID,
    
    -- 组件配置 (JSONB)
    weights_config JSONB NOT NULL DEFAULT '{}',
    prompt_config JSONB NOT NULL DEFAULT '{}',
    rag_config JSONB NOT NULL DEFAULT '{}',
    guardrails_config JSONB NOT NULL DEFAULT '{}',
    inference_params JSONB NOT NULL DEFAULT '{}',
    
    -- Lineage 信息
    parent_version_id UUID REFERENCES model_versions(id),
    forked_from UUID REFERENCES model_versions(id),
    
    -- 评估指标 (冗余存储，快速查询)
    evaluation_metrics JSONB DEFAULT '{}',
    
    tags VARCHAR(64)[] DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(name, version)
);

CREATE INDEX idx_model_versions_owner ON model_versions(owner_id);
CREATE INDEX idx_model_versions_status ON model_versions(status);
CREATE INDEX idx_model_versions_tags ON model_versions USING GIN(tags);
CREATE INDEX idx_model_versions_parent ON model_versions(parent_version_id);
CREATE INDEX idx_model_versions_created ON model_versions(created_at DESC);

-- GIN 索引用于 JSONB 查询
CREATE INDEX idx_model_versions_weights_config ON model_versions USING GIN(weights_config);
CREATE INDEX idx_model_versions_prompt_config ON model_versions USING GIN(prompt_config);
```

#### version_changelogs 表

```sql
CREATE TABLE version_changelogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    change_type VARCHAR(20) NOT NULL
        CHECK (change_type IN ('create', 'update', 'publish', 'rollback', 'archive')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    changes JSONB,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_changelogs_version ON version_changelogs(model_version_id);
CREATE INDEX idx_changelogs_created ON version_changelogs(created_at DESC);
```

---

### 3.3 Prompt 管理

#### prompt_templates 表

```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    owner_id UUID NOT NULL REFERENCES users(id),
    model_version_id UUID REFERENCES model_versions(id),
    current_version_id UUID,
    tags VARCHAR(64)[] DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompts_owner ON prompt_templates(owner_id);
CREATE INDEX idx_prompts_model_version ON prompt_templates(model_version_id);
CREATE INDEX idx_prompts_tags ON prompt_templates USING GIN(tags);
```

#### prompt_versions 表

```sql
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    commit_msg TEXT,
    branch_name VARCHAR(100) DEFAULT 'main',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(prompt_id, version)
);

CREATE INDEX idx_prompt_versions_prompt ON prompt_versions(prompt_id);
CREATE INDEX idx_prompt_versions_branch ON prompt_versions(branch_name);
CREATE INDEX idx_prompt_versions_created ON prompt_versions(created_at DESC);
```

---

### 3.4 RAG 知识库管理

#### knowledge_bases 表

```sql
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id),
    
    -- 向量化配置
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    embedding_dim INTEGER NOT NULL DEFAULT 1536,
    chunk_size INTEGER NOT NULL DEFAULT 512,
    chunk_overlap INTEGER NOT NULL DEFAULT 50,
    
    -- 向量数据库配置
    vector_db VARCHAR(50) DEFAULT 'milvus',
    vector_db_config JSONB DEFAULT '{}',
    
    -- 检索配置默认值
    default_top_k INTEGER DEFAULT 5,
    default_threshold DECIMAL(3,2) DEFAULT 0.8,
    
    tags VARCHAR(64)[] DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_kb_owner ON knowledge_bases(owner_id);
CREATE INDEX idx_kb_tags ON knowledge_bases USING GIN(tags);
```

#### documents 表

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),
    file_size BIGINT,
    mime_type VARCHAR(100),
    content_hash VARCHAR(64),
    status VARCHAR(20) NOT NULL DEFAULT 'uploading'
        CHECK (status IN ('uploading', 'parsing', 'chunking', 'embedding', 'ready', 'failed')),
    metadata JSONB DEFAULT '{}',
    chunk_count INTEGER DEFAULT 0,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_kb ON documents(kb_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created ON documents(created_at DESC);
```

#### chunks 表

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    vector_id VARCHAR(255),  -- Milvus 中的向量 ID
    chunk_index INTEGER NOT NULL,
    start_pos INTEGER,
    end_pos INTEGER,
    metadata JSONB DEFAULT '{}',
    token_count INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunks_doc ON chunks(doc_id);
CREATE INDEX idx_chunks_kb ON chunks(kb_id);
CREATE INDEX idx_chunks_vector_id ON chunks(vector_id);
CREATE INDEX idx_chunks_created ON chunks(created_at DESC);
```

---

### 3.5 工作流编排

#### workflows 表

```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id),
    
    -- DAG 定义 (JSONB)
    definition JSONB NOT NULL DEFAULT '{}',
    
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- 执行配置
    default_timeout INTEGER DEFAULT 300,  -- 秒
    retry_config JSONB DEFAULT '{}',
    
    tags VARCHAR(64)[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workflows_owner ON workflows(owner_id);
CREATE INDEX idx_workflows_active ON workflows(is_active);
CREATE INDEX idx_workflows_tags ON workflows USING GIN(tags);
```

#### workflow_runs 表

```sql
CREATE TABLE workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    workflow_version VARCHAR(50) NOT NULL,
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'scheduled', 'running', 'paused', 'success', 'failed', 'cancelled')),
    
    input_data JSONB DEFAULT '{}',
    output_data JSONB,
    error_details JSONB,
    
    current_step VARCHAR(255),
    duration_ms BIGINT,
    
    triggered_by UUID REFERENCES users(id),
    triggered_by_type VARCHAR(20) DEFAULT 'user',
    
    started_at TIMESTAMPTZ,
    scheduled_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workflow_runs_workflow ON workflow_runs(workflow_id);
CREATE INDEX idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX idx_workflow_runs_created ON workflow_runs(created_at DESC);
CREATE INDEX idx_workflow_runs_triggered ON workflow_runs(triggered_by);
```

#### step_executions 表

```sql
CREATE TABLE step_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    node_label VARCHAR(255),
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'success', 'failed', 'skipped')),
    
    input_data JSONB DEFAULT '{}',
    output_data JSONB,
    error_details TEXT,
    
    retry_count INTEGER DEFAULT 0,
    duration_ms INTEGER,
    
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_step_executions_run ON step_executions(run_id);
CREATE INDEX idx_step_executions_status ON step_executions(status);
CREATE INDEX idx_step_executions_node ON step_executions(node_id);
```

---

### 3.6 部署管理

#### deployments 表

```sql
CREATE TABLE deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    model_version_id UUID NOT NULL REFERENCES model_versions(id),
    environment VARCHAR(20) NOT NULL
        CHECK (environment IN ('development', 'staging', 'production')),
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'provisioning', 'deploying', 'running', 'scaling', 'failed', 'stopped')),
    
    -- 部署配置
    instance_type VARCHAR(100),
    min_replicas INTEGER DEFAULT 1,
    max_replicas INTEGER DEFAULT 10,
    current_replicas INTEGER DEFAULT 0,
    
    auto_scaling_config JSONB DEFAULT '{}',
    deployment_config JSONB DEFAULT '{}',
    
    -- 流量管理
    traffic_weight INTEGER DEFAULT 100,
    
    -- 端点信息
    endpoint_url VARCHAR(500),
    health_check_url VARCHAR(500),
    
    created_by UUID NOT NULL REFERENCES users(id),
    last_deployed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deployments_model_version ON deployments(model_version_id);
CREATE INDEX idx_deployments_environment ON deployments(environment);
CREATE INDEX idx_deployments_status ON deployments(status);
```

#### deployment_events 表

```sql
CREATE TABLE deployment_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id UUID NOT NULL REFERENCES deployments(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    message TEXT,
    metadata JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deployment_events_deployment ON deployment_events(deployment_id);
CREATE INDEX idx_deployment_events_created ON deployment_events(created_at DESC);
```

---

### 3.7 评估与监控

#### evaluations 表

```sql
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    evaluation_type VARCHAR(50) NOT NULL
        CHECK (evaluation_type IN ('hallucination', 'toxicity', 'faithfulness', 'relevance', 'comprehensive')),
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    
    -- 评估指标结果
    metrics JSONB NOT NULL DEFAULT '{}',
    
    -- 数据集信息
    dataset_id UUID,
    sample_size INTEGER NOT NULL DEFAULT 100,
    
    -- 失败样本详情
    failed_samples JSONB DEFAULT '[]',
    
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    duration_ms BIGINT,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evaluations_model_version ON evaluations(model_version_id);
CREATE INDEX idx_evaluations_type ON evaluations(evaluation_type);
CREATE INDEX idx_evaluations_status ON evaluations(status);
```

#### alerts 表

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL
        CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 关联资源
    resource_type VARCHAR(50),
    resource_id UUID,
    
    -- 告警规则详情
    rule_config JSONB DEFAULT '{}',
    current_value DECIMAL,
    threshold_value DECIMAL,
    
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'acknowledged', 'resolved', 'closed')),
    
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_resource ON alerts(resource_type, resource_id);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
```

---

### 3.8 审计日志

#### audit_logs 表

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    action_group VARCHAR(50),
    
    -- 资源信息
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    
    -- 用户信息
    user_id UUID REFERENCES users(id),
    user_name VARCHAR(100),
    
    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    
    -- 变更详情
    description TEXT,
    changes JSONB,  -- {old: {}, new: {}}
    
    -- 结果
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 按时间分区 (每月一个分区)
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

---

## 4. Redis 数据结构

### 4.1 缓存层

```
# 模型版本缓存
cache:mv:{id} → JSON string, TTL: 5 minutes

# Prompt 缓存
cache:prompt:{id} → JSON string, TTL: 10 minutes

# 用户会话
session:{token} → JSON user object, TTL: 24 hours
```

### 4.2 限流

```
# 基于 API Key 的限流
rate_limit:{api_key}:{minute} → counter, EXPIRE 60

# 基于 IP 的限流
rate_limit:ip:{ip}:{minute} → counter, EXPIRE 60
```

### 4.3 消息队列 (Stream)

```
# 任务队列
stream:tasks → [
  {id: "1", type: "quantization", model_version_id: "...", ...},
  ...
]

# 消费者组
XGROUP CREATE stream:tasks quantization_workers $ MKSTREAM
```

---

## 5. Milvus 向量设计

### 5.1 Collection 定义

```python
from pymilvus import Collection, CollectionSchema, FieldSchema, DataType

# Chunk 向量集合
chunk_fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
    FieldSchema(name="kb_id", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536),
    FieldSchema(name="chunk_index", dtype=DataType.INT32),
]

chunk_schema = CollectionSchema(fields=chunk_fields, description="Document chunks")
chunk_collection = Collection(name="chunks", schema=chunk_schema)

# 索引
index_params = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {"M": 16, "efConstruction": 256}
}
chunk_collection.create_index(field_name="vector", index_params=index_params)
```

### 5.2 分区策略

- 按 `kb_id` 分区，每个知识库一个分区
- 或者按时间分区（月度）

---

## 6. 数据库运维

### 6.1 备份策略

| 数据类型 | 备份频率 | 保留时间 | 备份方式 |
|---------|---------|---------|---------|
| PostgreSQL | 每日全量 + 增量 WAL | 30 天 | pg_basebackup + WAL-G |
| Redis | 每小时 RDB + AOF | 7 天 | RDB 快照 |
| Milvus | 每日 | 15 天 | 快照 + 数据导出 |
| MinIO | 版本控制 | 永久 | 内置版本控制 |

### 6.2 性能优化

**索引维护**
- 每周重建膨胀超过 30% 的索引
- 定期分析查询计划，优化慢查询

**分区表**
- `audit_logs` 按月分区，保留最近 12 个月
- `workflow_runs` 按月分区，保留最近 6 个月

**连接池**
- 使用 PgBouncer 做连接池
- 每个服务独立连接池配置

### 6.3 数据归档

- 超过 6 个月的运行日志归档到对象存储
- 超过 1 年的审计日志归档到冷存储
- 归档数据支持按需查询恢复

---

**文档结束**
