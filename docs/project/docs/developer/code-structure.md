# BeaverChain 代码结构说明

> 深入了解项目的架构设计和代码组织方式

---

## 📋 目录

1. [整体架构概览](#整体架构概览)
2. [后端代码结构](#后端代码结构)
3. [前端代码结构](#前端代码结构)
4. [核心模块设计](#核心模块设计)
5. [数据库设计](#数据库设计)
6. [API 设计规范](#api-设计规范)
7. [配置管理](#配置管理)

---

## 整体架构概览

### 分层架构

```
┌─────────────────────────────────────────────────┐
│                  前端层 (Frontend)               │
│  React + TypeScript + TailwindCSS + Vite        │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│                API 网关层 (API Gateway)          │
│  路由分发、认证授权、限流熔断、日志审计          │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│                微服务层 (Microservices)          │
├──────────┬──────────┬──────────┬──────────┬──────┤
│  版本控制 │  Prompt  │  编排引擎 │  评估服务 │ G    │
│  服务     │  服务     │          │          │      │
└──────────┴──────────┴──────────┴──────────┴──────┘
                         │
┌────────────────────────▼────────────────────────┐
│                数据访问层 (Data Access)          │
│  SQLAlchemy ORM + Redis Cache + Milvus 向量     │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│                数据存储层 (Storage)              │
│  PostgreSQL + Redis + MinIO/S3 + Milvus         │
└─────────────────────────────────────────────────┘
```

### 设计原则

1. **单一职责原则 (SRP)**：每个模块只负责一个功能领域
2. **依赖注入 (DI)**：通过构造函数注入依赖，便于测试和替换
3. **面向接口编程**：依赖抽象而非具体实现
4. **开闭原则 (OCP)**：对扩展开放，对修改关闭
5. **领域驱动设计 (DDD)**：按业务领域划分模块边界

---

## 后端代码结构

### 目录树

```
backend/
├── model_registry/              # 模型版本控制核心模块
│   ├── __init__.py
│   ├── main.py                  # FastAPI 应用入口 ✨
│   ├── requirements.txt         # Python 依赖
│   │
│   ├── models/                  # 数据模型层
│   │   ├── __init__.py
│   │   ├── schemas.py           # Pydantic Schema（请求/响应验证）
│   │   └── entities.py          # SQLAlchemy ORM 实体
│   │
│   ├── services/                # 业务服务层
│   │   ├── __init__.py
│   │   ├── database.py          # 数据库服务 - CRUD + 版本对比
│   │   ├── storage.py           # 存储服务 - 本地 / S3 / 分片上传
│   │   ├── versioning.py        # 版本控制逻辑
│   │   └── comparison.py        # 版本对比逻辑
│   │
│   ├── api/                     # API 层
│   │   ├── __init__.py
│   │   ├── routes.py            # FastAPI 路由定义
│   │   ├── dependencies.py      # 路由依赖注入
│   │   └── middleware.py        # 中间件（日志、CORS、认证等）
│   │
│   ├── core/                    # 核心基础设施
│   │   ├── __init__.py
│   │   ├── config.py            # 配置管理
│   │   ├── security.py          # 安全相关（JWT、密码等）
│   │   ├── logging.py           # 日志配置
│   │   └── exceptions.py        # 自定义异常
│   │
│   ├── tests/                   # 测试套件
│   │   ├── __init__.py
│   │   ├── conftest.py          # pytest 配置和 fixture
│   │   ├── test_database.py     # 数据库服务测试
│   │   ├── test_storage.py      # 存储服务测试
│   │   └── test_api.py          # API 端点测试
│   │
│   └── examples/                # 使用示例
│       ├── __init__.py
│       ├── sdk_usage.py         # Python SDK 示例
│       └── cli_tool.py          # 命令行工具示例
│
├── prompt_service/              # Prompt 管理服务（类似结构）
├── workflow_service/            # 工作流编排服务（类似结构）
├── evaluation_service/          # 评估监控服务（类似结构）
│
└── shared/                      # 共享库
    ├── __init__.py
    ├── constants.py             # 常量定义
    ├── utils.py                 # 通用工具函数
    └── schemas.py               # 共享 Pydantic Schema
```

### 分层详细说明

#### 1. API 层 (`api/`)

**职责**：处理 HTTP 请求，参数验证，路由分发

**设计要点**：
- 路由函数只做参数解析和响应格式化
- 业务逻辑委托给 Service 层
- 使用 Pydantic 进行请求/响应验证

**示例代码**：

```python
# api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from model_registry.services.database import DatabaseService
from model_registry.models.schemas import (
    ModelVersionCreate, ModelVersionResponse
)
from model_registry.api.dependencies import get_db_service

router = APIRouter(prefix="/model-versions", tags=["model-versions"])

@router.post("", response_model=ModelVersionResponse, status_code=201)
async def create_version(
    data: ModelVersionCreate,
    db_service: DatabaseService = Depends(get_db_service)
):
    """创建模型版本"""
    try:
        version = await db_service.create_version(data)
        return version
    except VersionAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

#### 2. 业务服务层 (`services/`)

**职责**：核心业务逻辑实现，事务管理，领域规则

**设计要点**：
- 每个 Service 类只负责一个领域
- 方法只做一件事，保持单一职责
- 不依赖 Web 框架，可独立测试

**示例代码**：

```python
# services/database.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from model_registry.models.entities import ModelVersionEntity
from model_registry.models.schemas import ModelVersionCreate, ModelVersionUpdate

class DatabaseService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_version(self, data: ModelVersionCreate) -> ModelVersionEntity:
        """创建模型版本"""
        # 1. 验证版本号是否已存在
        if await self._version_exists(data.name, data.version):
            raise VersionAlreadyExistsError(
                f"Version {data.version} already exists for {data.name}"
            )
        
        # 2. 创建实体
        entity = ModelVersionEntity(**data.model_dump())
        
        # 3. 保存到数据库
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        
        return entity
    
    async def compare_versions(
        self,
        base_id: str,
        target_id: str
    ) -> VersionComparison:
        """对比两个版本的差异"""
        base = await self.get_version(base_id)
        target = await self.get_version(target_id)
        
        if not base or not target:
            raise VersionNotFoundError()
        
        # 计算差异（递归比较所有字段）
        return self._calculate_difference(base, target)
```

#### 3. 数据模型层 (`models/`)

**职责**：定义数据结构，ORM 映射，验证规则

**设计要点**：
- Pydantic Schema：API 层数据验证
- SQLAlchemy ORM：数据库持久化
- 分离读写模型，避免过度耦合

**示例代码**：

```python
# models/schemas.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ModelVersionBase(BaseModel):
    """基础模型版本 Schema"""
    name: str = Field(..., description="模型名称", min_length=1, max_length=100)
    version: str = Field(..., description="版本号 (semver 格式)", min_length=1)
    description: Optional[str] = Field(None, description="版本描述")
    status: str = Field("draft", description="版本状态")
    
    @field_validator('version')
    @classmethod
    def validate_semver(cls, v: str) -> str:
        """验证 semver 格式"""
        import semver
        try:
            semver.VersionInfo.parse(v)
        except ValueError:
            raise ValueError(f"Invalid semver format: {v}")
        return v

class ModelVersionCreate(ModelVersionBase):
    """创建模型版本请求 Schema"""
    weights_config: Optional[Dict[str, Any]] = None
    prompt_config: Optional[Dict[str, Any]] = None
    rag_config: Optional[Dict[str, Any]] = None
    guardrails_config: Optional[Dict[str, Any]] = None
    inference_params: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)

class ModelVersionResponse(ModelVersionBase):
    """模型版本响应 Schema"""
    id: str
    evaluation_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # 支持 ORM 模型转换
```

#### 4. 核心基础设施层 (`core/`)

**职责**：配置管理、日志、安全、异常处理

**示例代码**：

```python
# core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库
    database_url: str = "sqlite:///./beaverchain.db"
    db_echo: bool = False
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    
    # 对象存储
    s3_endpoint: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_bucket: str = "beaverchain"
    
    # 应用
    debug: bool = False
    environment: str = "development"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例）"""
    return Settings()
```

---

## 前端代码结构

### 目录树

```
frontend/
├── src/
│   ├── main.tsx                 # 应用入口
│   ├── App.tsx                  # 根组件
│   ├── vite-env.d.ts            # Vite 类型定义
│   │
│   ├── components/              # 通用组件库
│   │   ├── ui/                 # 基础 UI 组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Table.tsx
│   │   │   └── Card.tsx
│   │   ├── layout/             # 布局组件
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Container.tsx
│   │   └── features/           # 业务组件
│   │       ├── ModelVersionCard.tsx
│   │       ├── PromptEditor.tsx
│   │       ├── WorkflowCanvas.tsx
│   │       └── MetricChart.tsx
│   │
│   ├── pages/                  # 页面组件
│   │   ├── Dashboard.tsx       # 仪表盘
│   │   ├── ModelVersions.tsx   # 模型版本列表
│   │   ├── ModelVersionDetail.tsx
│   │   ├── PromptLibrary.tsx   # Prompt 库
│   │   ├── Workflows.tsx       # 工作流编排
│   │   ├── Evaluations.tsx     # 评估监控
│   │   ├── Settings.tsx        # 设置页面
│   │   └── Login.tsx           # 登录页
│   │
│   ├── hooks/                  # 自定义 React Hooks
│   │   ├── useApi.ts           # API 调用封装
│   │   ├── useAuth.ts          # 认证相关
│   │   ├── useDebounce.ts      # 防抖
│   │   └── useLocalStorage.ts  # 本地存储
│   │
│   ├── services/               # API 服务层
│   │   ├── api.ts             # Axios 实例配置
│   │   ├── modelVersions.ts   # 模型版本 API
│   │   ├── prompts.ts         # Prompt API
│   │   ├── workflows.ts       # 工作流 API
│   │   └── evaluations.ts     # 评估 API
│   │
│   ├── stores/                 # 状态管理 (Zustand)
│   │   ├── useAuthStore.ts    # 认证状态
│   │   ├── useModelStore.ts   # 模型版本状态
│   │   └── useUISettings.ts   # UI 设置
│   │
│   ├── types/                  # TypeScript 类型定义
│   │   ├── api.ts             # API 相关类型
│   │   ├── models.ts          # 业务模型类型
│   │   └── common.ts          # 通用类型
│   │
│   ├── utils/                  # 工具函数
│   │   ├── format.ts          # 格式化函数
│   │   ├── validation.ts      # 验证函数
│   │   ├── date.ts            # 日期处理
│   │   └── constants.ts       # 常量定义
│   │
│   ├── styles/                 # 全局样式
│   │   ├── globals.css        # 全局 CSS
│   │   └── theme.ts           # 主题配置
│   │
│   └── lib/                    # 第三方库封装
│       ├── axios.ts           # Axios 配置
│       └── reactFlow.ts       # React Flow 配置
│
├── public/                     # 静态资源
│   ├── favicon.ico
│   └── logos/
│
├── tests/                      # 测试目录
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── e2e/                   # E2E 测试
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

### 前端架构模式

#### 1. 数据获取层 (Services + Hooks)

```typescript
// services/modelVersions.ts
import api from './api'
import type { ModelVersion, CreateVersionRequest } from '@/types/models'

export const modelVersionsApi = {
  async list(params?: { status?: string; page?: number }) {
    const response = await api.get<{
      items: ModelVersion[]
      total: number
      page: number
      page_size: number
    }>('/api/v1/model-versions', { params })
    return response.data
  },

  async get(id: string) {
    const response = await api.get<ModelVersion>(
      `/api/v1/model-versions/${id}`
    )
    return response.data
  },

  async create(data: CreateVersionRequest) {
    const response = await api.post<ModelVersion>(
      '/api/v1/model-versions',
      data
    )
    return response.data
  },

  async compare(baseId: string, targetId: string) {
    const response = await api.get(
      `/api/v1/model-versions/compare?base_id=${baseId}&target_id=${targetId}`
    )
    return response.data
  }
}
```

```typescript
// hooks/useModelVersions.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { modelVersionsApi } from '@/services/modelVersions'

export function useModelVersions(params?: { status?: string }) {
  return useQuery({
    queryKey: ['modelVersions', params],
    queryFn: () => modelVersionsApi.list(params)
  })
}

export function useModelVersion(id: string) {
  return useQuery({
    queryKey: ['modelVersion', id],
    queryFn: () => modelVersionsApi.get(id),
    enabled: !!id
  })
}

export function useCreateVersion() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: modelVersionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelVersions'] })
    }
  })
}
```

#### 2. 状态管理 (Zustand)

```typescript
// stores/useAuthStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  
  // Actions
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      
      login: (token, user) => set({
        token,
        user,
        isAuthenticated: true
      }),
      
      logout: () => set({
        token: null,
        user: null,
        isAuthenticated: false
      }),
      
      updateUser: (userData) => set((state) => ({
        user: state.user ? { ...state.user, ...userData } : null
      }))
    }),
    {
      name: 'auth-storage' // localStorage key
    }
  )
)
```

#### 3. 组件设计模式

```typescript
// components/features/ModelVersionCard.tsx
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import type { ModelVersion } from '@/types/models'
import { formatDate } from '@/utils/date'

interface ModelVersionCardProps {
  version: ModelVersion
  onEdit?: (id: string) => void
  onDelete?: (id: string) => void
  onRollback?: (id: string) => void
}

export function ModelVersionCard({
  version,
  onEdit,
  onDelete,
  onRollback
}: ModelVersionCardProps) {
  const statusColors = {
    draft: 'bg-gray-100 text-gray-800',
    testing: 'bg-yellow-100 text-yellow-800',
    staging: 'bg-blue-100 text-blue-800',
    production: 'bg-green-100 text-green-800',
    archived: 'bg-gray-50 text-gray-500'
  }

  return (
    <Card className="w-full hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">{version.name}</h3>
            <p className="text-sm text-gray-500">v{version.version}</p>
          </div>
          <Badge className={statusColors[version.status]}>
            {version.status}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <p className="text-gray-600 mb-4">{version.description}</p>
        
        <div className="text-sm text-gray-500">
          <p>创建时间: {formatDate(version.created_at)}</p>
          {version.tags.length > 0 && (
            <div className="flex gap-2 mt-2">
              {version.tags.map(tag => (
                <Badge key={tag} variant="secondary">{tag}</Badge>
              ))}
            </div>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="flex justify-end gap-2">
        <Button variant="secondary" size="sm" onClick={() => onEdit?.(version.id)}>
          编辑
        </Button>
        {version.status !== 'archived' && (
          <Button variant="secondary" size="sm" onClick={() => onRollback?.(version.id)}>
            回滚
          </Button>
        )}
        <Button variant="danger" size="sm" onClick={() => onDelete?.(version.id)}>
          删除
        </Button>
      </CardFooter>
    </Card>
  )
}
```

---

## 核心模块设计

### 版本控制模块

#### 核心概念

```
版本 (Version)
  ├── 名称 (name)
  ├── 版本号 (version) - semver 格式
  ├── 状态 (status) - draft/testing/staging/production/archived
  ├── 配置组件
  │   ├── WeightsConfig - 模型权重配置
  │   ├── PromptConfig - Prompt 模板
  │   ├── RAGConfig - RAG 知识库配置
  │   ├── GuardrailsConfig - 安全护栏配置
  │   └── InferenceParams - 推理参数
  ├── 评估指标 (evaluation_metrics)
  ├── 血缘信息 (lineage) - 父版本、派生方式
  └── 标签 (tags)
```

#### 版本对比算法

```python
# services/comparison.py
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class Difference:
    field: str
    type: str  # 'added', 'removed', 'modified'
    old_value: Any
    new_value: Any

@dataclass
class VersionComparison:
    base_version: Dict[str, Any]
    target_version: Dict[str, Any]
    differences: List[Difference]
    summary: Dict[str, int]

class VersionComparator:
    def compare(
        self,
        base: Dict[str, Any],
        target: Dict[str, Any],
        path: str = ""
    ) -> List[Difference]:
        """递归对比两个版本的配置"""
        differences = []
        
        # 获取所有键
        all_keys = set(base.keys()) | set(target.keys())
        
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            base_value = base.get(key)
            target_value = target.get(key)
            
            # 键已删除
            if key not in target:
                differences.append(Difference(
                    field=current_path,
                    type="removed",
                    old_value=base_value,
                    new_value=None
                ))
            
            # 键已添加
            elif key not in base:
                differences.append(Difference(
                    field=current_path,
                    type="added",
                    old_value=None,
                    new_value=target_value
                ))
            
            # 两者都有 - 递归比较
            elif isinstance(base_value, dict) and isinstance(target_value, dict):
                nested_diffs = self.compare(base_value, target_value, current_path)
                differences.extend(nested_diffs)
            
            # 值已修改
            elif base_value != target_value:
                differences.append(Difference(
                    field=current_path,
                    type="modified",
                    old_value=base_value,
                    new_value=target_value
                ))
        
        return differences
```

---

## 数据库设计

### 核心表结构

```sql
-- 模型版本表
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    owner_id UUID NOT NULL,
    project_id UUID,
    
    -- 配置组件 (JSONB)
    weights_config JSONB,
    prompt_config JSONB,
    rag_config JSONB,
    guardrails_config JSONB,
    inference_params JSONB,
    
    -- 评估指标
    evaluation_metrics JSONB,
    
    -- 血缘信息
    parent_version_id UUID REFERENCES model_versions(id),
    derived_from VARCHAR(50),
    
    -- 标签
    tags VARCHAR(255)[] DEFAULT '{}',
    
    -- 元数据
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,  -- 软删除
    
    -- 约束
    UNIQUE(name, version, deleted_at),  -- 同一名字+版本只能有一个未删除记录
    CHECK (status IN ('draft', 'testing', 'staging', 'production', 'archived'))
);

-- 索引
CREATE INDEX idx_model_versions_name ON model_versions(name);
CREATE INDEX idx_model_versions_status ON model_versions(status);
CREATE INDEX idx_model_versions_owner ON model_versions(owner_id);
CREATE INDEX idx_model_versions_tags ON model_versions USING GIN(tags);
CREATE INDEX idx_model_versions_created ON model_versions(created_at DESC);
```

### 数据库迁移（Alembic）

```python
# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from model_registry.models.entities import Base
from model_registry.core.config import get_settings

config = context.config
settings = get_settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = settings.database_url
    
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## API 设计规范

### RESTful 设计原则

1. **资源命名**：使用复数名词，如 `/model-versions`
2. **HTTP 方法语义**：
   - `GET`：获取资源
   - `POST`：创建资源
   - `PUT`：全量更新
   - `PATCH`：部分更新
   - `DELETE`：删除资源

3. **统一响应格式**：
   ```json
   {
     "success": true | false,
     "data": { /* 响应数据 */ },
     "error": { /* 错误详情 */ },
     "requestId": "req_abc123",
     "timestamp": "2026-05-12T14:30:00Z"
   }
   ```

4. **分页规范**：
   ```
   GET /api/v1/model-versions?page=1&page_size=20
   
   Response:
   {
     "items": [...],
     "total": 156,
     "page": 1,
     "page_size": 20,
     "total_pages": 8
   }
   ```

### 错误码设计

| HTTP 状态码 | 错误类型 | 场景 |
|------------|---------|------|
| 400 | BAD_REQUEST | 参数错误、格式错误 |
| 401 | UNAUTHORIZED | 未认证、Token 过期 |
| 403 | FORBIDDEN | 无权限 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突（如版本已存在） |
| 422 | VALIDATION_ERROR | 参数验证失败 |
| 429 | TOO_MANY_REQUESTS | 限流 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 📚 相关文档

- [贡献指南](contributing.md) - 如何参与项目开发
- [调试技巧](debugging.md) - 问题排查与调试方法
- [API 参考手册](../api/README.md) - 完整 API 文档

---

*文档版本: v1.0*
*最后更新: 2026-05-12*
