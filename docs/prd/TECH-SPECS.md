# BeaverChain 技术需求说明

**文档版本**: v1.0  
**创建日期**: 2026-05-12  
**技术评审**: Frank

---

## 1. 系统架构设计

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         客户端层                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ Web 控制台  │  │ Python SDK  │  │ JS/TS SDK   │  │ CLI 工具  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API 网关层                                    │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  认证授权  │  限流熔断  │  日志审计  │  请求路由  │  协议转换 │ │
│  └───────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        微服务层                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 版本控制服务 │  │ Prompt 服务  │  │ 编排服务     │               │
│  │ (go)         │  │ (go)         │  │ (go + python)│               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 评估服务     │  │ 部署服务     │  │ Guardrails   │               │
│  │ (python)     │  │ (go)         │  │ 服务 (go)    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        数据层                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Postgres │  │  Redis   │  │  Milvus  │  │  S3/OSS  │            │
│  │ (元数据) │  │ (缓存队列)│  │ (向量)   │  │ (文件存储)│            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        模型运行时                                    │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    Kubernetes 集群                              │ │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐               │ │
│  │  │ vLLM   │  │ TGI    │  │ 自定义  │  │ 评估   │               │ │
│  │  │ Pod    │  │ Pod    │  │ Pod     │  │ Worker│               │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 架构设计原则

**1. 微服务拆分原则**
- 按业务域拆分服务，每个服务有清晰的边界
- 服务间通过 gRPC 通信，API 网关统一对外暴露 REST API
- 无状态服务设计，支持水平扩展
- 每个服务独立数据库，避免跨库事务

**2. 高可用设计**
- 多区域部署，避免单点故障
- 服务自动健康检查和故障转移
- 关键数据多副本备份
- 优雅降级机制，核心功能优先

**3. 可观测性**
- 统一日志标准（结构化 JSON）
- 全链路追踪（OpenTelemetry）
- 关键指标监控（RED 方法）
- 告警分级和自动通知

**4. 安全性**
- 零信任架构，服务间也需要认证
- 数据传输加密（TLS 1.3）
- 静态数据加密（AES-256）
- 定期安全审计和漏洞扫描

---

## 2. 前端技术规格

### 2.1 技术栈选型

| 技术 | 版本 | 选型理由 |
|------|------|---------|
| **React** | 18.x | 生态成熟，团队熟悉，hooks 模式高效 |
| **TypeScript** | 5.x | 类型安全，减少运行时错误，IDE 支持好 |
| **TailwindCSS** | v4 | 原子化 CSS，开发效率高，一致的设计系统 |
| **React Query** | 5.x | 数据获取和缓存，自动重试和背景刷新 |
| **React Flow** | 11.x | Workflow 可视化编排，成熟稳定 |
| **TanStack Table** | 8.x | 高性能数据表格，功能丰富 |
| **Zod** | 3.x | 类型安全的表单验证 |
| **Lucide React** | latest | 轻量级图标库，风格统一 |
| **Vite** | 5.x | 极速构建，热更新快，开发体验好 |

### 2.2 项目结构

```
frontend/
├── src/
│   ├── components/          # 通用组件
│   │   ├── ui/             # 基础 UI 组件 (Button, Input, etc.)
│   │   ├── layout/         # 布局组件
│   │   └── features/       # 业务组件
│   ├── pages/              # 页面组件
│   │   ├── models/         # 模型版本管理
│   │   ├── prompts/        # Prompt 管理
│   │   ├── workflows/      # 编排引擎
│   │   ├── evaluations/    # 评估监控
│   │   └── settings/       # 设置页面
│   ├── hooks/              # 自定义 React Hooks
│   ├── services/           # API 服务层
│   ├── stores/             # 状态管理 (Zustand)
│   ├── types/              # TypeScript 类型定义
│   ├── utils/              # 工具函数
│   ├── lib/                # 第三方库封装
│   ├── styles/             # 全局样式
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.ts
```

### 2.3 状态管理策略

- **服务端状态**：使用 React Query 管理 API 数据、缓存、重试
- **客户端全局状态**：使用 Zustand（轻量级，简单高效）
- **复杂表单状态**：使用 React Hook Form + Zod
- **本地 UI 状态**：使用 React useState/useReducer

### 2.4 性能要求

| 指标 | 要求 | 测量方式 |
|------|------|---------|
| 首屏加载时间 | < 2 秒 | Lighthouse |
| FCP (First Contentful Paint) | < 1.5 秒 | Lighthouse |
| LCP (Largest Contentful Paint) | < 2.5 秒 | Lighthouse |
| TTI (Time to Interactive) | < 3.5 秒 | Lighthouse |
| 包大小 (gzip) | < 200 KB | 构建统计 |
| 路由切换时间 | < 100 ms | 性能监控 |

---

## 3. 后端技术规格

### 3.1 技术栈选型

| 技术 | 版本 | 用途 |
|------|------|------|
| **Go** | 1.22 | API 服务、业务逻辑、高并发场景 |
| **Gin** | 1.9 | HTTP 框架，高性能 |
| **gRPC** | 1.6 | 服务间高性能通信 |
| **Python** | 3.11 | ML 相关服务、评估计算、工具链集成 |
| **FastAPI** | 0.109 | Python API 框架，自动文档 |
| **PostgreSQL** | 16 | 关系型数据库，存储元数据 |
| **Redis** | 7.2 | 缓存、会话、任务队列、限流 |
| **Milvus** | 2.3 | 向量数据库，RAG 检索 |
| **MinIO** | latest | 对象存储，模型权重、文件 |

### 3.2 服务拆分

#### 3.2.1 版本控制服务 (version-service)

**职责**
- 模型版本 CRUD
- 版本快照和回滚
- 版本对比和差异计算
- Lineage 追踪

**数据库设计**
```sql
CREATE TABLE model_versions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL,
    owner_id UUID NOT NULL,
    weights_config JSONB,
    prompt_config JSONB,
    rag_config JSONB,
    guardrails_config JSONB,
    parameters JSONB,
    tags VARCHAR(255)[],
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(name, version)
);

CREATE INDEX idx_model_versions_owner ON model_versions(owner_id);
CREATE INDEX idx_model_versions_status ON model_versions(status);
CREATE INDEX idx_model_versions_tags ON model_versions USING GIN(tags);
```

#### 3.2.2 Prompt 服务 (prompt-service)

**职责**
- Prompt CRUD 和版本化
- Prompt 模板管理
- 分支管理和合并
- Prompt 测试执行

**关键接口**
```
POST   /api/v1/prompts              # 创建 Prompt
GET    /api/v1/prompts/:id          # 获取 Prompt
PUT    /api/v1/prompts/:id          # 更新 Prompt
GET    /api/v1/prompts/:id/versions # 版本列表
POST   /api/v1/prompts/:id/branches # 创建分支
POST   /api/v1/prompts/:id/test     # 测试 Prompt
```

#### 3.2.3 编排服务 (workflow-service)

**职责**
- Workflow 定义 CRUD
- 工作流执行引擎
- 任务调度和状态管理
- Lineage 数据收集

**执行状态机**
```
PENDING → RUNNING → SUCCESS
                → FAILED
                → CANCELLED
                → PAUSED → RUNNING
```

#### 3.2.4 评估服务 (evaluation-service)

**职责**
- 幻觉检测
- 毒性评分
- 忠实度计算
- 质量指标聚合
- 评估报告生成

**评估算法**
- 幻觉检测：基于事实一致性检查 + 自一致性验证
- 毒性检测：集成 Perspective API + 本地分类器
- 忠实度：基于嵌入相似度 + 语义对齐评分

#### 3.2.5 部署服务 (deployment-service)

**职责**
- 多环境部署管理
- Kubernetes 资源编排
- 灰度发布和流量控制
- 自动扩缩容
- 部署状态监控

#### 3.2.6 Guardrails 服务 (guardrails-service)

**职责**
- 内容安全检查
- 敏感词过滤
- 输出格式验证
- 规则动态配置
- 实时规则更新

### 3.3 API 设计规范

#### REST API 规范

**URL 设计**
- 使用名词复数：`/api/v1/model-versions`
- 层级关系清晰：`/api/v1/models/:id/versions`
- 查询参数用于过滤、排序、分页

**HTTP 方法**
```
GET    /resource          # 列表查询
GET    /resource/:id      # 单个查询
POST   /resource          # 创建
PUT    /resource/:id      # 全量更新
PATCH  /resource/:id      # 部分更新
DELETE /resource/:id      # 删除
```

**统一响应格式**
```json
{
  "success": true,
  "data": { /* 响应数据 */ },
  "error": null,
  "requestId": "req_abc123",
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
  "requestId": "req_abc123",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

#### gRPC 服务间通信

**协议定义示例**
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

## 4. 数据架构

### 4.1 数据库选型策略

| 数据类型 | 存储方案 | 理由 |
|---------|---------|------|
| **业务元数据** | PostgreSQL | 关系型数据，需要事务，查询灵活 |
| **缓存/会话** | Redis | 高性能，支持过期，多种数据结构 |
| **向量数据** | Milvus | 专门优化的向量检索，ANN 算法 |
| **大文件/模型权重** | S3/OSS/MinIO | 成本低，可扩展，CDN 加速 |
| **日志/事件** | ClickHouse | 列式存储，OLAP 查询快 |
| **时序指标** | Prometheus + Thanos | 监控指标，降采样，长期存储 |

### 4.2 PostgreSQL 设计规范

**命名规范**
- 表名：小写 + 下划线，复数形式 `model_versions`
- 字段名：小写 + 下划线 `created_at`
- 索引名：`idx_table_column` 或 `idx_table_column1_column2`
- 外键：`fk_table_refcolumn`

**必备字段**
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
deleted_at TIMESTAMPTZ  -- 软删除
```

**索引策略**
- 主键自动索引
- 外键必须建索引
- 频繁查询的过滤条件建索引
- JSONB 字段使用 GIN 索引
- 联合索引注意最左前缀原则

### 4.3 Redis 使用规范

**Key 命名规范**
```
<service>:<resource>:<id>[:<suffix>]

示例：
version:model:abc123:meta
prompt:template:common:cache
workflow:execution:xyz789:state
```

**数据结构选型**
- String：简单 KV、计数器
- Hash：对象字段
- List：队列、时间线
- Set：去重集合
- ZSet：排行榜、有序集合
- Stream：消息队列（新方案优先）

---

## 5. 部署与运维

### 5.1 Kubernetes 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                     Ingress Controller                   │
│              (Nginx / ALB, SSL 终止)                    │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                     Service Mesh                         │
│                   (Istio 可选)                           │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ API Pod │      │Workflow │      │ vLLM    │
   │ (HPA)   │      │ Pod     │      │ GPU Pod │
   └─────────┘      └─────────┘      └─────────┘
```

### 5.2 扩缩容策略

| 服务类型 | 扩缩容指标 | 目标值 |
|---------|-----------|-------|
| **API 服务** | CPU 使用率 | 70% |
| | 内存使用率 | 80% |
| | 请求队列长度 | 100 |
| **工作流 Worker** | 队列积压数 | 1000 |
| **推理服务 (GPU)** | GPU 利用率 | 80% |
| | 排队请求数 | 50 |

### 5.3 监控与告警

**核心指标 (RED 方法)**
- Rate：每秒请求数
- Errors：错误率
- Duration：响应时间分布

**告警分级**
```
P0 (Critical)   - 系统不可用，立即响应（< 5 分钟）
  - 服务错误率 > 5% 持续 5 分钟
  - API 网关 5xx > 10%
  - 数据库连接耗尽

P1 (High)       - 严重影响，1 小时内响应
  - 单个实例不可用
  - 响应时间 P95 > 2s
  - 磁盘使用率 > 85%

P2 (Medium)     - 一般问题，工作时间处理
  - 内存使用率 > 80%
  - 非核心接口变慢
  - 证书 30 天内过期

P3 (Low)        - 优化建议，有空处理
  - 各种建议性告警
```

---

## 6. 安全要求

### 6.1 认证与授权

**认证方式**
- 用户认证：JWT Token，短期有效 + Refresh Token
- 服务间认证：mTLS 或 Service Account Token
- API 访问：API Key + 签名
- 管理后台：SSO（OAuth2 / SAML）

**授权模型**
```
RBAC + ABAC 混合模型

角色层级：
  Owner → Admin → Editor → Viewer

权限粒度：
  - 组织级
  - 项目级
  - 资源级（单个模型版本）

细粒度控制：
  - 基于标签的权限
  - 基于环境的权限（生产/测试）
  - 基于时间的权限
```

### 6.2 数据安全

**传输安全**
- 强制 TLS 1.3，禁用旧版本
- 内部服务间也启用 TLS
- 证书自动续期（cert-manager）

**静态加密**
- 数据库透明数据加密 (TDE)
- 对象存储服务端加密
- 敏感字段应用层加密（AES-256-GCM）

**数据脱敏**
- 日志中不输出敏感数据
- API 响应按需脱敏
- 导出数据自动脱敏

### 6.3 合规要求

| 合规项 | 要求 | 实现方式 |
|-------|------|---------|
| **审计日志** | 所有写操作留痕 | 统一审计日志服务 |
| **数据留存** | 操作日志 ≥ 1 年 | 对象存储归档 |
| **访问控制** | 最小权限原则 | RBAC + 定期权限审计 |
| **漏洞扫描** | 每月一次 | 自动化扫描工具 |
| **渗透测试** | 每季度一次 | 第三方安全公司 |

---

## 7. 开发流程规范

### 7.1 Git 工作流

```
main (生产环境)
  ↑
release/* (预发布分支)
  ↑
develop (开发环境)
  ↑
feature/* (功能分支)
bugfix/* (修复分支)
```

**提交规范** (Conventional Commits)
```
<type>(<scope>): <description>

type: feat, fix, docs, style, refactor, test, chore, perf
scope: 模块名，如 version, workflow, api

示例：
feat(version): 支持模型权重关联
fix(prompt): 修复编辑器变量高亮 bug
docs: 更新 API 文档
```

### 7.2 CI/CD 流水线

```
代码提交
   ↓
[代码检查]
   ├─ 静态代码分析 (golangci-lint, eslint)
   ├─ 安全扫描 (trivy, gosec)
   └─ 许可证检查
   ↓
[构建测试]
   ├─ 单元测试 (覆盖率 ≥ 80%)
   ├─ 集成测试
   ├─ E2E 测试
   └─ 性能基准测试
   ↓
[构建镜像]
   ├─ 多阶段构建
   ├─ 镜像扫描
   └─ 推送到镜像仓库
   ↓
[部署]
   ├─ 开发环境 (自动)
   ├─ 预发环境 (手动)
   └─ 生产环境 (审批后)
```

### 7.3 代码质量标准

| 指标 | 要求 |
|------|------|
| 单元测试覆盖率 | ≥ 80% |
| 静态代码检查 | 0 Error，Warning 需说明 |
| CI 流水线通过率 | 100% 才能合并 |
| Code Review | 至少 1 人批准 |
| 主分支保护 | 禁止直接推送 |

---

## 8. 技术债务管理

### 8.1 债务分类与处理

| 债务类型 | 优先级 | 处理策略 |
|---------|--------|---------|
| **安全债务** | P0 | 立即修复，不能超过 24 小时 |
| **性能债务** | P1 | 下个迭代修复 |
| **可维护性债务** | P2 | 安排在重构周处理 |
| **技术选型债务** | P3 | 大版本升级时统一处理 |

### 8.2 重构计划

- **每月第一个周五**：重构日，集中处理技术债务
- **每季度**：架构评审，识别潜在债务
- **大版本前**：技术债务清零点，不欠账上线

---

**文档结束**
