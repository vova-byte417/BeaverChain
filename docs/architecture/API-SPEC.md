# BeaverChain API 接口规范

**文档版本**: v1.0  
**创建日期**: 2026-05-12  
**架构师**: Charlie

---

## 1. API 设计规范

### 1.1 基础信息

- **Base URL**: `https://api.beaverchain.com/v1`
- **认证方式**: Bearer Token (JWT) / API Key
- **数据格式**: JSON
- **字符编码**: UTF-8
- **时间格式**: ISO 8601 (`2026-05-12T10:30:00Z`)

### 1.2 统一响应格式

**成功响应 (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "example-model"
  },
  "request_id": "req_abc123xyz",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

**列表响应 (200 OK)**
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
  "request_id": "req_abc123xyz",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

**创建成功 (201 Created)**
```json
{
  "success": true,
  "data": { "id": "..." },
  "request_id": "req_abc123xyz",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

**错误响应 (4xx/5xx)**
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
  "request_id": "req_abc123xyz",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

### 1.3 错误码定义

| HTTP 状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | BAD_REQUEST | 请求参数错误 |
| 400 | VALIDATION_ERROR | 数据验证失败 |
| 401 | UNAUTHORIZED | 未认证或认证失效 |
| 403 | FORBIDDEN | 权限不足 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突（如版本号重复） |
| 422 | UNPROCESSABLE_ENTITY | 语义错误，无法处理 |
| 429 | TOO_MANY_REQUESTS | 请求限流 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务暂不可用 |

### 1.4 分页规范

**请求参数**
```
GET /api/v1/model-versions?page=1&page_size=20&sort=-created_at,name
```

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| page | integer | 否 | 1 | 页码，从 1 开始 |
| page_size | integer | 否 | 20 | 每页数量，最大 100 |
| sort | string | 否 | -created_at | 排序字段，- 表示降序 |

### 1.5 认证头部

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-API-Key: sk_live_abc123xyz789
```

---

## 2. 模型版本管理 API

### 2.1 创建模型版本

```http
POST /model-versions
Content-Type: application/json

{
  "name": "my-assistant",
  "version": "1.0.0",
  "description": "第一个稳定版本",
  "tags": ["production", "gpt-4"],
  "weights_config": {
    "model_type": "gpt4",
    "provider": "openai",
    "model_id": "gpt-4-turbo-preview",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 2048
    }
  },
  "prompt_config": {
    "system_prompt": "You are a helpful assistant...",
    "template_id": "pt_abc123"
  },
  "rag_config": {
    "knowledge_base_id": "kb_xyz789",
    "top_k": 5,
    "score_threshold": 0.8
  }
}
```

**响应 (201 Created)**
```json
{
  "success": true,
  "data": {
    "id": "mv_550e8400e29b41d4a716446655440000",
    "name": "my-assistant",
    "version": "1.0.0",
    "status": "draft",
    "created_at": "2026-05-12T10:30:00Z"
  }
}
```

### 2.2 获取模型版本列表

```http
GET /model-versions?page=1&page_size=20&status=production&tag=gpt-4
```

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 按状态过滤: draft/testing/production/archived |
| tag | string | 按标签过滤 |
| search | string | 搜索名称或描述 |
| owner_id | string | 按创建者过滤 |

### 2.3 获取模型版本详情

```http
GET /model-versions/{id}
```

**响应 (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "mv_550e8400e29b41d4a716446655440000",
    "name": "my-assistant",
    "version": "1.0.0",
    "description": "第一个稳定版本",
    "status": "production",
    "owner_id": "user_abc123",
    "tags": ["production", "gpt-4"],
    "weights_config": {...},
    "prompt_config": {...},
    "rag_config": {...},
    "guardrails_config": {...},
    "evaluation_metrics": {
      "hallucination_rate": 0.03,
      "toxicity_score": 0.05,
      "faithfulness": 0.95,
      "avg_latency_ms": 450
    },
    "created_at": "2026-05-12T10:30:00Z",
    "updated_at": "2026-05-12T11:00:00Z"
  }
}
```

### 2.4 更新模型版本

```http
PATCH /model-versions/{id}
Content-Type: application/json

{
  "description": "更新后的描述",
  "tags": ["production", "gpt-4", "v1"]
}
```

### 2.5 删除模型版本

```http
DELETE /model-versions/{id}
```

**响应 (204 No Content)**

### 2.6 发布模型版本

```http
POST /model-versions/{id}/publish
Content-Type: application/json

{
  "status": "production",
  "release_notes": "支持多轮对话，优化 RAG 检索效果"
}
```

### 2.7 回滚模型版本

```http
POST /model-versions/{id}/rollback
Content-Type: application/json

{
  "target_version_id": "mv_previous_version_id",
  "reason": "新版本幻觉率过高"
}
```

### 2.8 对比两个版本

```http
GET /model-versions/compare?base_id={base_id}&target_id={target_id}
```

**响应**
```json
{
  "success": true,
  "data": {
    "diff": {
      "weights_config": {
        "temperature": { "old": 0.7, "new": 0.5 },
        "max_tokens": { "old": 1024, "new": 2048 }
      },
      "prompt_config": {
        "system_prompt": { "changed": true }
      }
    },
    "metrics_comparison": {
      "hallucination_rate": { "old": 0.05, "new": 0.03, "change": -0.02 },
      "avg_latency_ms": { "old": 500, "new": 450, "change": -50 }
    }
  }
}
```

---

## 3. Prompt 管理 API

### 3.1 创建 Prompt

```http
POST /prompts
Content-Type: application/json

{
  "name": "客服助手 Prompt",
  "description": "用于客户服务的系统提示词",
  "content": "你是一个专业的客服助手... {{user_question}}",
  "variables": [
    {
      "name": "user_question",
      "type": "string",
      "description": "用户的问题",
      "required": true
    }
  ],
  "tags": ["customer-service", "v1"]
}
```

### 3.2 获取 Prompt 列表

```http
GET /prompts?page=1&page_size=20&tag=customer-service
```

### 3.3 获取 Prompt 详情

```http
GET /prompts/{id}
```

### 3.4 更新 Prompt

```http
PUT /prompts/{id}
Content-Type: application/json

{
  "name": "客服助手 Prompt v2",
  "content": "更新后的内容...",
  "commit_msg": "优化语气，更加友好"
}
```

### 3.5 获取 Prompt 版本历史

```http
GET /prompts/{id}/versions
```

### 3.6 测试 Prompt

```http
POST /prompts/{id}/test
Content-Type: application/json

{
  "variables": {
    "user_question": "如何退款？"
  },
  "model_version_id": "mv_abc123"
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "rendered_prompt": "你是一个专业的客服助手... 如何退款？",
    "model_output": "您好，关于退款流程...",
    "evaluation": {
      "toxicity_score": 0.01,
      "estimated_tokens": 350
    },
    "latency_ms": 420
  }
}
```

### 3.7 创建 Prompt 分支

```http
POST /prompts/{id}/branches
Content-Type: application/json

{
  "name": "feature/more-friendly",
  "description": "尝试更友好的语气"
}
```

---

## 4. RAG 知识库管理 API

### 4.1 创建知识库

```http
POST /knowledge-bases
Content-Type: application/json

{
  "name": "产品文档库",
  "description": "存储所有产品帮助文档",
  "embedding_model": "text-embedding-3-large",
  "chunk_size": 512,
  "chunk_overlap": 50
}
```

### 4.2 上传文档

```http
POST /knowledge-bases/{id}/documents
Content-Type: multipart/form-data

file: <binary-file-content>
metadata: {"source": "help-center", "category": "billing"}
```

### 4.3 添加文本内容

```http
POST /knowledge-bases/{id}/chunks
Content-Type: application/json

{
  "chunks": [
    {
      "content": "退款政策：购买后 30 天内可申请全额退款...",
      "metadata": {
        "page": "refund-policy",
        "last_updated": "2026-05-01"
      }
    }
  ]
}
```

### 4.4 检索知识库

```http
POST /knowledge-bases/{id}/search
Content-Type: application/json

{
  "query": "退款政策是什么？",
  "top_k": 5,
  "score_threshold": 0.8,
  "filters": {
    "category": "billing"
  }
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "chunk_abc123",
        "content": "退款政策：购买后 30 天内可申请全额退款...",
        "score": 0.95,
        "metadata": {...}
      }
    ]
  }
}
```

---

## 5. 工作流编排 API

### 5.1 创建 Workflow

```http
POST /workflows
Content-Type: application/json

{
  "name": "客服处理工作流",
  "description": "处理用户咨询的完整工作流",
  "definition": {
    "nodes": [
      {
        "id": "start",
        "type": "start",
        "label": "开始"
      },
      {
        "id": "classify",
        "type": "llm",
        "label": "意图识别",
        "config": {
          "model_version_id": "mv_abc123",
          "prompt": "分析用户问题的意图: {{user_input}}"
        }
      },
      {
        "id": "rag_retrieve",
        "type": "rag",
        "label": "知识库检索",
        "config": {
          "knowledge_base_id": "kb_xyz789"
        }
      },
      {
        "id": "generate_answer",
        "type": "llm",
        "label": "生成回答",
        "config": {
          "model_version_id": "mv_abc123"
        }
      },
      {
        "id": "end",
        "type": "end",
        "label": "结束"
      }
    ],
    "edges": [
      {"source": "start", "target": "classify"},
      {"source": "classify", "target": "rag_retrieve"},
      {"source": "rag_retrieve", "target": "generate_answer"},
      {"source": "generate_answer", "target": "end"}
    ]
  }
}
```

### 5.2 获取 Workflow 列表

```http
GET /workflows?page=1&page_size=20
```

### 5.3 执行 Workflow

```http
POST /workflows/{id}/runs
Content-Type: application/json

{
  "input_data": {
    "user_input": "我想退款",
    "user_id": "user_123"
  },
  "metadata": {
    "source": "api",
    "trace_id": "trace_abc123"
  }
}
```

**响应 (201 Created)**
```json
{
  "success": true,
  "data": {
    "run_id": "run_550e8400e29b41d4a716446655440000",
    "status": "running",
    "started_at": "2026-05-12T10:30:00Z"
  }
}
```

### 5.4 获取 Workflow 执行状态

```http
GET /workflows/runs/{run_id}
```

**响应**
```json
{
  "success": true,
  "data": {
    "run_id": "run_550e8400e29b41d4a716446655440000",
    "workflow_id": "wf_abc123",
    "status": "success",
    "current_step": "end",
    "input_data": {...},
    "output_data": {
      "answer": "您好，关于退款流程...",
      "confidence": 0.95
    },
    "step_executions": [
      {
        "node_id": "classify",
        "status": "success",
        "duration_ms": 150,
        "output": {...}
      }
    ],
    "total_duration_ms": 850,
    "started_at": "2026-05-12T10:30:00Z",
    "finished_at": "2026-05-12T10:30:01Z"
  }
}
```

### 5.5 获取 Workflow 执行历史

```http
GET /workflows/{id}/runs?page=1&page_size=20&status=success
```

---

## 6. 部署管理 API

### 6.1 创建部署

```http
POST /deployments
Content-Type: application/json

{
  "model_version_id": "mv_abc123",
  "environment": "production",
  "deployment_config": {
    "instance_type": "gpu-a10g",
    "min_replicas": 2,
    "max_replicas": 10,
    "auto_scaling": {
      "target_qps": 100,
      "scale_up_threshold": 0.8,
      "scale_down_threshold": 0.3
    }
  },
  "traffic_weight": 100
}
```

### 6.2 获取部署列表

```http
GET /deployments?environment=production
```

### 6.3 灰度发布 - 调整流量权重

```http
PATCH /deployments/{id}/traffic
Content-Type: application/json

{
  "traffic_weight": 50
}
```

### 6.4 回滚部署

```http
POST /deployments/{id}/rollback
Content-Type: application/json

{
  "reason": "新版本延迟过高"
}
```

---

## 7. 评估与监控 API

### 7.1 触发评估任务

```http
POST /evaluations
Content-Type: application/json

{
  "model_version_id": "mv_abc123",
  "evaluation_types": ["hallucination", "toxicity", "faithfulness"],
  "test_dataset_id": "ds_test_001",
  "options": {
    "sample_size": 100,
    "random_seed": 42
  }
}
```

### 7.2 获取评估结果

```http
GET /evaluations/{id}
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": "eval_abc123",
    "model_version_id": "mv_abc123",
    "status": "completed",
    "metrics": {
      "hallucination_rate": {
        "value": 0.03,
        "pass": true,
        "threshold": 0.05
      },
      "toxicity_score": {
        "value": 0.05,
        "pass": true,
        "threshold": 0.1
      },
      "faithfulness": {
        "value": 0.95,
        "pass": true,
        "threshold": 0.9
      }
    },
    "failed_samples": [
      {
        "input": "...",
        "output": "...",
        "reason": "检测到幻觉内容"
      }
    ],
    "started_at": "2026-05-12T10:00:00Z",
    "finished_at": "2026-05-12T10:15:00Z"
  }
}
```

### 7.3 获取质量仪表盘数据

```http
GET /monitoring/dashboard?time_range=7d
```

**响应**
```json
{
  "success": true,
  "data": {
    "time_range": "7d",
    "overview": {
      "total_requests": 125000,
      "avg_latency_ms": 420,
      "p95_latency_ms": 680,
      "error_rate": 0.005
    },
    "quality_metrics": {
      "hallucination_rate": {
        "current": 0.03,
        "trend": -0.01,
        "history": [...]
      },
      "toxicity_score": {
        "current": 0.05,
        "trend": 0.0,
        "history": [...]
      }
    },
    "cost_metrics": {
      "total_tokens": 52000000,
      "total_cost": 156.50,
      "avg_cost_per_request": 0.00125
    }
  }
}
```

### 7.4 获取告警列表

```http
GET /monitoring/alerts?status=active
```

---

## 8. Guardrails 安全护栏 API

### 8.1 配置 Guardrails 规则

```http
PUT /guardrails/config
Content-Type: application/json

{
  "toxicity_filter": {
    "enabled": true,
    "threshold": 0.7,
    "action": "reject"
  },
  "sensitive_words": {
    "enabled": true,
    "words": ["敏感词1", "敏感词2"],
    "action": "mask"
  },
  "hallucination_detection": {
    "enabled": true,
    "threshold": 0.5,
    "action": "warn"
  },
  "pii_detection": {
    "enabled": true,
    "types": ["email", "phone", "credit_card"],
    "action": "redact"
  }
}
```

### 8.2 获取 Guardrails 配置

```http
GET /guardrails/config
```

### 8.3 测试 Guardrails 规则

```http
POST /guardrails/test
Content-Type: application/json

{
  "input": "测试内容，包含敏感词...",
  "check_types": ["toxicity", "sensitive_words"]
}
```

---

## 9. 优化工具链 API

### 9.1 创建量化任务

```http
POST /optimizations/quantize
Content-Type: application/json

{
  "model_version_id": "mv_abc123",
  "quantization_type": "gptq",
  "bits": 4,
  "dataset": "c4",
  "group_size": 128,
  "description": "4-bit GPTQ 量化"
}
```

### 9.2 创建蒸馏任务

```http
POST /optimizations/distill
Content-Type: application/json

{
  "teacher_model_id": "mv_teacher_large",
  "student_model_id": "mv_student_small",
  "dataset_id": "ds_training_001",
  "hyperparameters": {
    "temperature": 2.0,
    "alpha": 0.7,
    "epochs": 3,
    "batch_size": 32
  }
}
```

### 9.3 获取优化任务状态

```http
GET /optimizations/tasks/{task_id}
```

**响应**
```json
{
  "success": true,
  "data": {
    "task_id": "opt_abc123",
    "type": "quantization",
    "status": "running",
    "progress": 65,
    "estimated_completion": "2026-05-12T12:00:00Z",
    "output_model_version_id": null
  }
}
```

### 9.4 获取优化前后对比

```http
GET /optimizations/tasks/{task_id}/comparison
```

---

## 10. Webhook API

### 10.1 创建 Webhook

```http
POST /webhooks
Content-Type: application/json

{
  "name": "部署状态通知",
  "url": "https://example.com/webhooks/beaverchain",
  "events": [
    "deployment.created",
    "deployment.status_changed",
    "model_version.published",
    "evaluation.completed",
    "alert.triggered"
  ],
  "secret": "whsec_your_signing_secret",
  "enabled": true,
  "description": "同步部署状态到内部系统"
}
```

### 10.2 获取 Webhook 列表

```http
GET /webhooks
```

### 10.3 更新 Webhook

```http
PUT /webhooks/{id}
```

### 10.4 删除 Webhook

```http
DELETE /webhooks/{id}
```

---

## 11. SDK 使用示例

### 11.1 Python SDK

```python
from beaverchain import BeaverChain

# 初始化客户端
client = BeaverChain(api_key="sk_live_abc123")

# 创建模型版本
version = client.model_versions.create(
    name="my-assistant",
    version="1.0.0",
    weights_config={
        "model_type": "gpt4",
        "provider": "openai",
        "model_id": "gpt-4-turbo-preview"
    }
)

# 执行 Workflow
result = client.workflows.run(
    workflow_id="wf_abc123",
    input_data={"user_input": "我想退款"}
)

print(f"回答: {result.output_data['answer']}")
print(f"耗时: {result.total_duration_ms}ms")
```

### 11.2 JavaScript SDK

```javascript
import { BeaverChain } from '@beaverchain/sdk';

const client = new BeaverChain({ apiKey: 'sk_live_abc123' });

// 检索知识库
const results = await client.knowledgeBases.search('kb_xyz789', {
  query: '退款政策是什么？',
  topK: 5
});

console.log('检索结果:', results);
```

---

## 12. 速率限制

| 层级 | 请求限制 | 说明 |
|------|---------|------|
| **Free** | 100 请求/分钟 | 免费试用 |
| **Basic** | 1000 请求/分钟 | 基础版 |
| **Pro** | 10000 请求/分钟 | 专业版 |
| **Enterprise** | 可定制 | 企业版 |

超过限制返回 `429 Too Many Requests`，包含 `Retry-After` 头部。

---

**文档结束**
