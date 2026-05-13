# BeaverChain API 参考手册

> 完整的 REST API 文档，包含所有端点的详细说明

---

## 📋 目录

1. [基础信息](#基础信息)
2. [认证方式](#认证方式)
3. [模型版本 API](#模型版本-api)
4. [文件上传 API](#文件上传-api)
5. [Prompt API](#prompt-api)
6. [RAG 知识库 API](#rag-知识库-api)
7. [工作流 API](#工作流-api)
8. [评估监控 API](#评估监控-api)
9. [错误处理](#错误处理)
10. [速率限制](#速率限制)

---

## 基础信息

### API 端点

| 环境 | Base URL |
|------|----------|
| 本地开发 | `http://localhost:8000/api/v1` |
| 测试环境 | `https://staging-api.beaverchain.ai/api/v1` |
| 生产环境 | `https://api.beaverchain.ai/api/v1` |

### 数据格式

- **请求格式**: JSON (`Content-Type: application/json`)
- **响应格式**: JSON
- **字符编码**: UTF-8

### 统一响应格式

#### 成功响应
```json
{
  "success": true,
  "data": { /* 返回数据 */ },
  "requestId": "req_abc123xyz",
  "timestamp": "2026-05-12T14:30:00Z"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "版本号格式错误",
    "details": [
      { "field": "version", "reason": "必须符合 semver 格式" }
    ]
  },
  "requestId": "req_abc123xyz",
  "timestamp": "2026-05-12T14:30:00Z"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| `200 OK` | 请求成功 |
| `201 Created` | 创建成功 |
| `400 Bad Request` | 请求参数错误 |
| `401 Unauthorized` | 认证失败 |
| `403 Forbidden` | 权限不足 |
| `404 Not Found` | 资源不存在 |
| `409 Conflict` | 资源冲突 |
| `422 Unprocessable Entity` | 验证失败 |
| `429 Too Many Requests` | 超出速率限制 |
| `500 Internal Server Error` | 服务器内部错误 |

---

## 认证方式

### API Key 认证

在请求头中添加：

```http
Authorization: Bearer your-api-key-here
```

### 获取 API Key

1. 登录 BeaverChain 控制台
2. 进入 **「设置」→「API 密钥」**
3. 点击 **「生成新密钥」**
4. 保存密钥（只会显示一次）

⚠️ **安全提示**:
- 不要在代码中硬编码 API Key
- 使用环境变量存储密钥
- 定期轮换密钥
- 如果密钥泄露，立即撤销

---

## 模型版本 API

### 创建模型版本

```http
POST /api/v1/model-versions
Content-Type: application/json
Authorization: Bearer your-api-key
```

**请求体:**
```json
{
  "name": "customer-support",
  "version": "1.0.0",
  "description": "客服助手 v1.0.0",
  "status": "draft",
  "weights_config": {
    "model_type": "llama2",
    "path": "s3://models/llama2-7b/",
    "quantization": "4bit"
  },
  "prompt_config": {
    "template": "你是一个{{role}}助手。用户问题：{{user_query}}",
    "variables": ["role", "user_query"],
    "default_values": { "role": "专业的" }
  },
  "rag_config": {
    "enabled": true,
    "knowledge_base_id": "kb-123",
    "top_k": 3,
    "similarity_threshold": 0.7
  },
  "guardrails_config": {
    "toxicity_threshold": 0.5,
    "hallucination_check": true
  },
  "inference_params": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 1024
  },
  "tags": ["production", "customer-service"]
}
```

**响应 (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "mv-abc123xyz",
    "name": "customer-support",
    "version": "1.0.0",
    "status": "draft",
    "created_at": "2026-05-12T14:30:00Z",
    "updated_at": "2026-05-12T14:30:00Z"
  },
  "requestId": "req_abc123"
}
```

---

### 列出模型版本

```http
GET /api/v1/model-versions?status=production&page=1&page_size=20
Authorization: Bearer your-api-key
```

**查询参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 否 | 按名称过滤 |
| `status` | string | 否 | 按状态过滤 (draft/testing/staging/production/archived) |
| `tag` | string | 否 | 按标签过滤 |
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页数量，默认 20，最大 100 |
| `sort_by` | string | 否 | 排序字段 (created_at/name/version) |
| `sort_order` | string | 否 | 排序方向 (asc/desc)，默认 desc |

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "mv-abc123",
        "name": "customer-support",
        "version": "1.0.0",
        "status": "production",
        "description": "客服助手",
        "tags": ["production"],
        "created_at": "2026-05-12T14:30:00Z"
      }
    ],
    "total": 15,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  },
  "requestId": "req_abc123"
}
```

---

### 获取版本详情

```http
GET /api/v1/model-versions/{id}
Authorization: Bearer your-api-key
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "mv-abc123",
    "name": "customer-support",
    "version": "1.0.0",
    "description": "客服助手 v1.0.0",
    "status": "production",
    "weights_config": { /* ... */ },
    "prompt_config": { /* ... */ },
    "rag_config": { /* ... */ },
    "guardrails_config": { /* ... */ },
    "inference_params": { /* ... */ },
    "evaluation_metrics": {
      "hallucination_rate": 0.035,
      "toxicity_score": 0.05,
      "faithfulness": 0.96,
      "average_latency_ms": 320
    },
    "tags": ["production"],
    "lineage": {
      "parent_version_id": "mv-parent456",
      "derived_from": "manual-edit"
    },
    "created_at": "2026-05-12T14:30:00Z",
    "updated_at": "2026-05-12T14:35:00Z",
    "owner_id": "user-789"
  },
  "requestId": "req_abc123"
}
```

---

### 更新版本

```http
PATCH /api/v1/model-versions/{id}
Content-Type: application/json
Authorization: Bearer your-api-key
```

**请求体:** (只需要包含要更新的字段)
```json
{
  "status": "production",
  "description": "更新描述",
  "tags": ["production", "v1-stable"]
}
```

---

### 删除版本

```http
DELETE /api/v1/model-versions/{id}
Authorization: Bearer your-api-key
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": { "deleted": true, "id": "mv-abc123" },
  "requestId": "req_abc123"
}
```

---

### 对比两个版本

```http
GET /api/v1/model-versions/compare?base_id={base_id}&target_id={target_id}
Authorization: Bearer your-api-key
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "base_version": { "id": "mv-1", "version": "1.0.0" },
    "target_version": { "id": "mv-2", "version": "1.1.0" },
    "differences": [
      {
        "field": "prompt_config.template",
        "type": "modified",
        "old_value": "旧模板...",
        "new_value": "新模板..."
      },
      {
        "field": "inference_params.temperature",
        "type": "modified",
        "old_value": 0.7,
        "new_value": 0.5
      }
    ],
    "summary": {
      "total_changes": 2,
      "modified": 2,
      "added": 0,
      "removed": 0
    }
  },
  "requestId": "req_abc123"
}
```

---

### 回滚版本

```http
POST /api/v1/model-versions/{id}/rollback
Content-Type: application/json
Authorization: Bearer your-api-key
```

**请求体:**
```json
{
  "target_version_id": "mv-target123",
  "reason": "性能下降，回滚到上一稳定版本",
  "create_new_version": true,
  "new_version_suffix": "rollback"
}
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "rolled_back": true,
    "new_version_id": "mv-new456",
    "from_version": "mv-target123",
    "reason": "性能下降，回滚到上一稳定版本"
  },
  "requestId": "req_abc123"
}
```

---

### 获取版本历史

```http
GET /api/v1/model-versions/history/{name}
Authorization: Bearer your-api-key
```

**查询参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `limit` | int | 否 | 返回数量，默认 20 |

---

### 获取统计信息

```http
GET /api/v1/model-versions/statistics/summary
Authorization: Bearer your-api-key
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_versions": 156,
    "by_status": {
      "draft": 45,
      "testing": 23,
      "staging": 12,
      "production": 67,
      "archived": 9
    },
    "total_unique_models": 42,
    "storage_used_bytes": 107374182400,
    "last_7_days_changes": 28
  },
  "requestId": "req_abc123"
}
```

---

## 文件上传 API

### 简单文件上传（< 50MB）

```http
POST /api/v1/model-versions/upload/simple
Content-Type: multipart/form-data
Authorization: Bearer your-api-key
```

**请求体:**
```
--boundary
Content-Disposition: form-data; name="file"; filename="model_weights.bin"
Content-Type: application/octet-stream

<binary data>
--boundary
Content-Disposition: form-data; name="path"

models/customer-support/v1/
--boundary--
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "file_id": "file-abc123",
    "path": "models/customer-support/v1/model_weights.bin",
    "size_bytes": 10485760,
    "sha256": "abcdef123456...",
    "created_at": "2026-05-12T14:30:00Z"
  },
  "requestId": "req_abc123"
}
```

---

### 大文件分片上传

#### 步骤 1: 初始化分片上传

```http
POST /api/v1/model-versions/upload/init
Content-Type: application/json
Authorization: Bearer your-api-key
```

**请求体:**
```json
{
  "filename": "large_model_weights.bin",
  "path": "models/customer-support/v1/",
  "total_size_bytes": 8589934592,
  "chunk_size_bytes": 5242880
}
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "upload_id": "upload-xyz789",
    "chunk_size_bytes": 5242880,
    "total_chunks": 1639,
    "expires_at": "2026-05-13T14:30:00Z"
  },
  "requestId": "req_abc123"
}
```

#### 步骤 2: 上传分片

```http
POST /api/v1/model-versions/upload/chunk
Content-Type: multipart/form-data
Authorization: Bearer your-api-key
```

**请求体:**
```
--boundary
Content-Disposition: form-data; name="upload_id"

upload-xyz789
--boundary
Content-Disposition: form-data; name="chunk_index"

1
--boundary
Content-Disposition: form-data; name="chunk_data"; filename="chunk_001.bin"
Content-Type: application/octet-stream

<binary chunk data>
--boundary--
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "chunk_index": 1,
    "received": true,
    "uploaded_chunks": 1,
    "remaining_chunks": 1638
  },
  "requestId": "req_abc123"
}
```

#### 步骤 3: 完成上传

```http
POST /api/v1/model-versions/upload/complete
Content-Type: application/json
Authorization: Bearer your-api-key
```

**请求体:**
```json
{
  "upload_id": "upload-xyz789"
}
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "file_id": "file-abc123",
    "path": "models/customer-support/v1/large_model_weights.bin",
    "size_bytes": 8589934592,
    "sha256": "abcdef123456...",
    "chunks_uploaded": 1639,
    "created_at": "2026-05-12T14:35:00Z"
  },
  "requestId": "req_abc123"
}
```

---

### 文件下载

```http
GET /api/v1/model-versions/files/{path}
Authorization: Bearer your-api-key
```

**响应:** 文件二进制流

### 获取文件元数据

```http
GET /api/v1/model-versions/files/{path}/metadata
Authorization: Bearer your-api-key
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "file_id": "file-abc123",
    "path": "models/customer-support/v1/model_weights.bin",
    "size_bytes": 10485760,
    "sha256": "abcdef123456...",
    "created_at": "2026-05-12T14:30:00Z",
    "last_modified": "2026-05-12T14:30:00Z"
  },
  "requestId": "req_abc123"
}
```

---

### 检查文件是否存在

```http
GET /api/v1/model-versions/files/{path}/exists
Authorization: Bearer your-api-key
```

**响应 (200 OK):**
```json
{
  "success": true,
  "data": {
    "exists": true,
    "file_id": "file-abc123",
    "size_bytes": 10485760
  },
  "requestId": "req_abc123"
}
```

---

## 健康检查 API

### 服务健康状态

```http
GET /health
```

**响应 (200 OK):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime": "3d 12h 45m 30s",
  "timestamp": "2026-05-12T14:30:00Z"
}
```

### 数据库健康状态

```http
GET /health/db
```

**响应 (200 OK):**
```json
{
  "status": "ok",
  "database": "postgresql",
  "connection_pool": {
    "active": 5,
    "idle": 10,
    "max_size": 20
  },
  "latency_ms": 2.5
}
```

---

## 错误处理

### 错误码列表

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| `VALIDATION_ERROR` | 422 | 请求参数验证失败 |
| `AUTHENTICATION_FAILED` | 401 | API Key 无效或过期 |
| `PERMISSION_DENIED` | 403 | 没有权限访问该资源 |
| `NOT_FOUND` | 404 | 请求的资源不存在 |
| `RESOURCE_CONFLICT` | 409 | 资源冲突（如版本号已存在） |
| `RATE_LIMIT_EXCEEDED` | 429 | 超出速率限制 |
| `FILE_TOO_LARGE` | 413 | 文件大小超过限制 |
| `INVALID_FILE_TYPE` | 415 | 不支持的文件类型 |
| `UPLOAD_EXPIRED` | 410 | 上传会话已过期 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务暂时不可用 |

---

## 速率限制

### 限制规则

| 端点类型 | 速率限制 |
|----------|---------|
| 读操作 (GET) | 1000 次/分钟 |
| 写操作 (POST/PUT/PATCH/DELETE) | 200 次/分钟 |
| 文件上传 | 10 次/分钟 |
| 大文件分片上传 | 100 次/分钟 |

### 响应头

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 985
X-RateLimit-Reset: 1715524200
Retry-After: 60
```

### 超出限制响应

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60
```

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "超出速率限制，请稍后重试",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_in_seconds": 60
    }
  },
  "requestId": "req_abc123",
  "timestamp": "2026-05-12T14:30:00Z"
}
```

---

## SDK 使用示例

### Python SDK

```python
from beaverchain import ModelRegistryClient

# 初始化客户端
client = ModelRegistryClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# 创建版本
version = client.create_version({
    "name": "my-assistant",
    "version": "1.0.0",
    "status": "draft",
    "prompt_config": {
        "template": "你是一个有帮助的助手",
        "variables": []
    }
})

# 列出所有版本
versions = client.list_versions(status="production")

# 获取版本详情
detail = client.get_version(version["id"])

# 对比版本
diff = client.compare_versions(version_a_id, version_b_id)

# 回滚版本
rolled_back = client.rollback_version(
    version_id=current_version_id,
    target_version_id=previous_version_id,
    reason="性能问题"
)
```

---

## 📚 相关文档

- [Python SDK 文档](python-sdk.md) - 完整的 Python SDK 使用指南
- [代码示例](../developer/code-examples.md) - 丰富的代码示例
- [常见问题](../user/faq.md) - API 使用常见问题解答

---

*文档版本: v1.0*
*最后更新: 2026-05-12*
