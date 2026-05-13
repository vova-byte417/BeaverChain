# BeaverChain 常见问题 (FAQ)

> 这里汇总了使用 BeaverChain 过程中最常见的问题和解决方案

---

## 📋 目录

1. [安装与部署](#安装与部署)
2. [模型版本管理](#模型版本管理)
3. [Prompt 管理](#prompt-管理)
4. [RAG 知识库](#rag-知识库)
5. [工作流编排](#工作流编排)
6. [API 集成](#api-集成)
7. [性能优化](#性能优化)
8. [安全与权限](#安全与权限)
9. [故障排查](#故障排查)

---

## 安装与部署

### Q: 最低系统要求是什么？

**A:** 运行 BeaverChain 的最低要求：

- **CPU**: 4 核
- **内存**: 8 GB
- **磁盘**: 50 GB 可用空间
- **操作系统**: Linux (推荐 Ubuntu 22.04)、macOS 13+、Windows 10/11

如需运行 LLM 推理，建议：
- GPU: NVIDIA RTX 3090+ 或同等性能
- GPU 内存: 24 GB+

---

### Q: 如何在本地快速启动？

**A:** 使用 Docker Compose 一键启动：

```bash
# 1. 克隆代码
git clone https://github.com/vova-byte417/BeaverChain.git
cd BeaverChain

# 2. 复制配置文件
cp .env.example .env

# 3. 启动所有服务
docker compose up -d

# 4. 访问 Web 界面
open http://localhost:3000

# 默认账号
# 邮箱: admin@beaverchain.ai
# 密码: admin123
```

---

### Q: 启动后无法访问怎么办？

**A:** 按以下步骤排查：

```bash
# 1. 检查容器状态
docker compose ps

# 2. 如果有容器未启动，查看日志
docker compose logs backend
docker compose logs frontend
docker compose logs postgres

# 3. 检查端口是否被占用
netstat -anp | grep -E ':(3000|8000|5432)'

# 4. 检查防火墙
sudo ufw status
```

常见原因：
- 端口 3000 或 8000 被占用
- PostgreSQL 未正常启动
- 环境变量配置错误
- 防火墙阻止了连接

---

### Q: 如何升级到最新版本？

**A:** 按以下步骤安全升级：

```bash
# 1. 备份数据库
docker compose exec postgres pg_dump -U postgres beaverchain > backup_$(date +%Y%m%d).sql

# 2. 拉取最新镜像
docker compose pull

# 3. 停止旧服务
docker compose down

# 4. 启动新服务
docker compose up -d

# 5. 执行数据库迁移（如需要）
docker compose exec backend python manage.py migrate

# 6. 验证升级
curl http://localhost:8000/health
```

---

## 模型版本管理

### Q: 版本号有什么规范？

**A:** 建议遵循 [语义化版本 (SemVer)](https://semver.org/lang/zh-CN/) 规范：

```
主版本号.次版本号.修订号
  │        │        │
  │        │        └─ 向后兼容的 Bug 修复
  │        └─────────── 向后兼容的功能新增
  └──────────────────── 不兼容的 API 变更
```

**示例：**
- `1.0.0` - 初始正式版本
- `1.0.1` - 修复 Bug
- `1.1.0` - 新增功能
- `2.0.0` - 重大变更

也可以添加预发布标签：
- `1.0.0-alpha` - Alpha 测试版
- `1.0.0-beta` - Beta 测试版
- `1.0.0-rc1` - 发布候选版

---

### Q: 如何回滚到历史版本？

**A:** 有两种回滚方式：

**方式一：创建新版本（推荐，保留历史）**

```python
# Python SDK 示例
client.rollback_version(
    version_id="current-version-id",
    target_version_id="previous-version-id",
    reason="新 Prompt 效果不佳，回滚到稳定版",
    create_new_version=True,
    new_version_suffix="rollback"  # 生成类似 1.0.1-rollback 的版本号
)
```

**方式二：原地回滚（慎用，会覆盖当前版本）**

```python
client.rollback_version(
    version_id="current-version-id",
    target_version_id="previous-version-id",
    create_new_version=False  # 原地回滚
)
```

---

### Q: 支持哪些存储后端？

**A:** 目前支持以下存储后端：

| 存储类型 | 说明 | 适用场景 |
|---------|------|---------|
| **本地文件系统** | 默认，无需额外配置 | 开发测试、小型部署 |
| **MinIO** | 自建对象存储 | 私有部署、数据本地化 |
| **AWS S3** | 亚马逊对象存储 | 云上部署、高可用 |
| **阿里云 OSS** | 阿里云对象存储 | 国内云环境 |
| **腾讯云 COS** | 腾讯云对象存储 | 国内云环境 |

**配置示例：**

```env
# 本地文件系统
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=/data/beaverchain

# MinIO / S3
STORAGE_TYPE=s3
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET=beaverchain
S3_REGION=us-east-1
```

---

### Q: 大文件上传失败怎么办？

**A:** 对于超过 500MB 的文件，建议使用分片上传：

```python
# Python SDK - 大文件分片上传
client.upload_large_file(
    file_path="/path/to/large_model.bin",
    chunk_size=5*1024*1024,  # 5MB 分片
    max_retries=3
)
```

常见问题及解决：
1. **超时**：增加超时时间 `timeout=3600`
2. **断点续传**：SDK 自动支持，中断后重新运行即可
3. **内存不足**：减小分片大小，如 `chunk_size=1*1024*1024`

---

## Prompt 管理

### Q: Prompt 变量如何使用？

**A:** 使用 `{{变量名}}` 语法定义变量：

```
你是一个专业的 {{role}}，名叫 {{name}}。

用户问题：{{user_query}}

请用友好、专业的语气回答：
```

**变量类型：**

```python
# 字符串变量
{"role": "客服", "name": "Beaver"}

# 列表变量（循环使用）
{"topics": ["产品介绍", "价格说明", "使用帮助"]}

# 对象变量
{"user": {"name": "张三", "level": "VIP"}}
```

---

### Q: 如何进行 A/B 测试？

**A:** 按以下步骤设置 A/B 测试：

1. **准备两个 Prompt 版本**
   - Version A: 现有 Prompt（对照组）
   - Version B: 优化后的 Prompt（实验组）

2. **创建 A/B 测试**

```python
experiment = client.create_ab_test(
    name="客服话术优化",
    versions=["version-a-id", "version-b-id"],
    traffic_split=[0.5, 0.5],  # 50% / 50% 流量分配
    metrics=["user_satisfaction", "response_time", "completion_rate"]
)
```

3. **运行测试并分析结果**

```python
# 获取实验报告
report = client.get_ab_test_report(experiment.id)

print(f"版本 A 满意度: {report.version_a.metrics.user_satisfaction:.2f}")
print(f"版本 B 满意度: {report.version_b.metrics.user_satisfaction:.2f}")
print(f"统计显著性: {report.statistical_significance}")

# 选择优胜版本
if report.version_b.metrics.user_satisfaction > report.version_a.metrics.user_satisfaction:
    print("版本 B 更优！")
    client.promote_version(version_b_id, "production")
```

---

### Q: Prompt 支持条件分支吗？

**A:** 支持！使用 `{% if %}` 语法：

```
你是一个客服助手。

用户等级：{{user_level}}

{% if user_level == "VIP" %}
你好尊贵的 VIP 用户，我将优先为您服务。
首先向您致歉，然后立即安排专人为您解决问题。
{% elif user_level == "PREMIUM" %}
您好高级会员，很高兴为您服务。
请详细描述您遇到的问题，我会尽快处理。
{% else %}
您好用户，感谢您的咨询。
请按以下步骤自助排查...
{% endif %}

问题：{{user_query}}
```

---

## RAG 知识库

### Q: 支持哪些文件格式？

**A:** 目前支持：

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| **PDF** | `.pdf` | 自动提取文本 |
| **Word** | `.docx`, `.doc` | 需要 libreoffice |
| **Markdown** | `.md`, `.markdown` | 完美支持 |
| **纯文本** | `.txt`, `.log` | 完全支持 |
| **网页** | URL | 自动抓取内容 |
| **PPT** | `.pptx` | 提取文本内容 |

---

### Q: 如何提高检索准确率？

**A:** 可以从以下几个方面优化：

1. **优化文档分块**
   ```python
   # 语义分块（推荐）
   chunker = SemanticChunker(
       chunk_size=512,
       chunk_overlap=50,
       separator="\n\n"
   )
   
   # 按标题分块
   chunker = TitleChunker(
       level_separators=["#", "##", "###"]
   )
   ```

2. **使用重排序 (Rerank)**
   ```python
   search_config = {
       "top_k": 20,  # 先检索更多结果
       "rerank": True,
       "rerank_top_k": 5,  # 然后重排序取前 5 个
       "rerank_model": "bge-reranker-large"
   }
   ```

3. **混合检索 (关键词 + 向量)**
   ```python
   search_config = {
       "hybrid_search": True,
       "keyword_weight": 0.3,
       "vector_weight": 0.7
   }
   ```

4. **查询改写 (Query Rewrite)**
   ```python
   # 让 LLM 优化用户查询
   rewritten_query = llm(f"""
   请将用户问题改写为更适合检索的关键词：
   用户问题：{{user_query}}
   改写后的查询：""")
   ```

---

### Q: 知识库更新后如何生效？

**A:** BeaverChain 支持增量更新：

```python
# 添加新文档
knowledge_base.add_document(new_documents)

# 更新已有文档
knowledge_base.update_document(doc_id, new_content)

# 删除文档
knowledge_base.delete_document(doc_id)

# 全量重建（慎用，适合小数据集）
knowledge_base.rebuild()
```

**更新后立即生效**，无需重启服务。

---

## 工作流编排

### Q: 工作流支持哪些节点类型？

**A:** 目前支持以下节点类型：

| 节点类型 | 图标 | 用途 |
|---------|------|------|
| **开始/结束** | ⭕ | 工作流入口和出口 |
| **LLM** | 🤖 | 调用大模型处理 |
| **条件分支** | 🔀 | 根据条件选择路径 |
| **知识库检索** | 🔍 | 从 RAG 知识库检索 |
| **代码执行** | 💻 | 运行 Python/JS 代码 |
| **HTTP 请求** | 🌐 | 调用外部 API |
| **子工作流** | 📦 | 嵌套调用其他工作流 |
| **合并** | 🔗 | 合并多个分支结果 |
| **工具调用** | 🛠️ | 调用内置工具 |

---

### Q: 如何调试工作流？

**A:** 使用内置的调试功能：

1. **单步执行**
   - 在工作流编辑器中点击"调试模式"
   - 可以逐个节点执行
   - 查看每个节点的输入输出

2. **断点调试**
   - 在关键节点设置断点
   - 工作流运行到断点时暂停
   - 检查中间状态和变量

3. **执行日志**
   ```python
   # 获取工作流执行详情
   execution = client.get_workflow_execution(execution_id)
   
   # 查看每个节点的执行日志
   for step in execution.steps:
       print(f"节点: {step.name}")
       print(f"状态: {step.status}")
       print(f"输入: {step.input}")
       print(f"输出: {step.output}")
       if step.error:
           print(f"错误: {step.error}")
   ```

---

### Q: 工作流支持并行执行吗？

**A:** 支持！有两种并行模式：

1. **分支并行**
   ```
   [开始]
      │
      ├───────┬───────┐
      ▼       ▼       ▼
   [任务A]  [任务B]  [任务C]  ← 并行执行
      └───────┴───────┘
              │
              ▼
          [合并结果]
   ```

2. **循环并行**
   ```python
   # 对列表中的每个元素并行执行处理
   workflow.add_parallel_loop(
       items="{{input_list}}",
       processor_node=llm_node,
       max_workers=5  # 最大并发数
   )
   ```

---

## API 集成

### Q: API 调用频率有限制吗？

**A:** 是的，默认限流规则：

| API 类型 | 限制 |
|---------|------|
| 读操作 (GET) | 1000 次/分钟 |
| 写操作 (POST/PUT/PATCH) | 200 次/分钟 |
| 文件上传 | 10 次/分钟 |
| 大文件分片 | 100 次/分钟 |

超过限制会返回 `429 Too Many Requests`。

**企业版**可以调整限流阈值，请联系客服。

---

### Q: 如何处理 API 错误？

**A:** 建议使用如下错误处理模式：

```python
import time
from beaverchain.exceptions import ApiError, RateLimitError

def safe_api_call(func, max_retries=3, backoff_factor=2):
    for attempt in range(max_retries):
        try:
            return func()
        
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_factor ** attempt
            print(f"限流，等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
        
        except ApiError as e:
            if e.status_code >= 500:
                if attempt == max_retries - 1:
                    raise
                time.sleep(backoff_factor ** attempt)
            else:
                # 4xx 错误不重试
                raise
        
        except Exception as e:
            print(f"未知错误: {e}")
            raise

# 使用
result = safe_api_call(lambda: client.create_version(data))
```

---

### Q: API 支持批量操作吗？

**A:** 支持！部分接口提供批量操作：

```python
# 批量创建版本
versions = client.create_versions_bulk([
    {"name": "model-a", "version": "1.0.0"},
    {"name": "model-b", "version": "1.0.0"},
    {"name": "model-c", "version": "1.0.0"}
])

# 批量删除
client.delete_versions_bulk(["id1", "id2", "id3"])

# 批量获取
versions = client.get_versions_bulk(["id1", "id2", "id3"])
```

批量操作的优势：
- 减少网络往返
- 提高吞吐量
- 原子性（全部成功或全部失败）

---

## 性能优化

### Q: 如何提高 API 响应速度？

**A:** 可以从以下方面优化：

1. **启用缓存**
   ```env
   CACHE_ENABLED=true
   CACHE_TTL=300  # 缓存 5 分钟
   ```

2. **使用连接池**
   ```python
   # Python SDK 配置连接池
   client = BeaverChainClient(
       api_key="your-key",
       connection_pool_size=50,
       max_connections=100
   )
   ```

3. **请求压缩**
   ```python
   # 启用 gzip 压缩
   client = BeaverChainClient(compression=True)
   ```

4. **异步调用**
   ```python
   # 使用异步客户端
   async with AsyncBeaverChainClient() as client:
       result = await client.create_version(data)
   ```

---

### Q: 数据库慢查询如何优化？

**A:** 按以下步骤优化：

1. **检查索引**
   ```sql
   -- 查看慢查询日志
   SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
   
   -- 检查索引使用情况
   SELECT 
       schemaname,
       tablename,
       indexname,
       idx_scan,
       idx_tup_read,
       idx_tup_fetch
   FROM pg_stat_user_indexes;
   ```

2. **添加缺失索引**
   ```sql
   -- 模型版本名称索引
   CREATE INDEX CONCURRENTLY idx_model_versions_name_trgm 
   ON model_versions USING gin (name gin_trgm_ops);
   
   -- 复合索引
   CREATE INDEX CONCURRENTLY idx_model_versions_status_created 
   ON model_versions(status, created_at DESC);
   ```

3. **优化查询**
   ```python
   # 只查询需要的字段
   versions = client.list_versions(
       fields=["id", "name", "version", "status"],  # 指定字段
       limit=20
   )
   
   # 使用游标分页（比 offset 分页更高效）
   versions = client.list_versions(
       cursor="last_id_value",
       limit=20
   )
   ```

---

## 安全与权限

### Q: 如何配置角色权限？

**A:** BeaverChain 使用 RBAC（基于角色的访问控制）：

**预设角色：**

| 角色 | 权限 | 适用场景 |
|------|------|---------|
| **Owner** | 所有权限 | 项目所有者 |
| **Admin** | 管理成员、配置 | 项目经理 |
| **Editor** | 编辑内容，不能删除 | 开发人员 |
| **Viewer** | 只读访问 | 访客、利益相关方 |
| **Guest** | 受限访问 | 外部协作者 |

**自定义角色示例：**

```python
# 创建自定义角色
client.create_role(
    name="Prompt Engineer",
    permissions=[
        "prompt.read",
        "prompt.create",
        "prompt.edit",
        "model_version.read",
        "evaluation.read"
    ]
)

# 给用户分配角色
client.assign_user_role(user_id, role_id)
```

---

### Q: API Key 如何安全管理？

**A:** 安全最佳实践：

1. **不要硬编码**
   ```python
   # ✅ 正确：使用环境变量
   import os
   api_key = os.getenv("BEAVERCHAIN_API_KEY")
   
   # ❌ 错误：硬编码
   api_key = "sk-1234567890abcdef"
   ```

2. **使用密钥管理服务**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets

3. **定期轮换**
   ```python
   # 创建新密钥
   new_key = client.create_api_key(name="new-production-key")
   
   # 平滑切换
   # 1. 同时使用新旧密钥一段时间
   # 2. 确认所有系统都使用新密钥
   # 3. 禁用旧密钥
   client.revoke_api_key(old_key_id)
   ```

4. **最小权限原则**
   每个 API Key 只授予必要的权限。

---

### Q: 数据加密如何配置？

**A:** BeaverChain 提供多层加密：

1. **传输加密 (TLS)**
   ```yaml
   # docker-compose.yml
   traefik:
     command:
       - --entrypoints.web.http.tls=true
       - --entrypoints.web.http.tls.certresolver=letsencrypt
   ```

2. **静态加密**
   ```env
   # 数据库字段加密
   ENCRYPTION_ENABLED=true
   ENCRYPTION_KEY=your-256-bit-key-here
   ```

3. **文件加密**
   ```env
   # 上传文件自动加密
   STORAGE_ENCRYPTION=true
   STORAGE_ENCRYPTION_KEY=your-encryption-key
   ```

---

## 故障排查

### Q: 页面加载失败，显示 502 Bad Gateway？

**A:** 通常是后端服务未正常启动：

```bash
# 1. 检查后端容器状态
docker compose ps backend

# 2. 查看后端日志
docker compose logs backend --tail=100

# 3. 常见错误：
# - 数据库连接失败：检查 DATABASE_URL
# - Redis 连接失败：检查 REDIS_URL
# - 端口被占用：检查 8000 端口

# 4. 重启后端服务
docker compose restart backend
```

---

### Q: 文件上传总是失败？

**A:** 按以下步骤排查：

```bash
# 1. 检查文件大小限制
# Nginx 配置
client_max_body_size 2G;

# 2. 检查磁盘空间
df -h

# 3. 检查存储服务日志
docker compose logs minio

# 4. 检查权限
ls -la /data/beaverchain/uploads
```

---

### Q: RAG 检索结果不准确？

**A:** 可能的原因和解决方案：

1. **文档分块不合理**
   - 检查分块大小是否合适（建议 256-1024 tokens）
   - 考虑使用语义分块而非固定大小

2. **嵌入模型不匹配**
   - 确保查询和文档使用相同的嵌入模型
   - 考虑使用领域微调的嵌入模型

3. **检索参数需要调优**
   - 调整 `top_k` 数量
   - 调整相似度阈值
   - 启用重排序 (Rerank)

4. **知识库质量问题**
   - 清理重复文档
   - 移除低质量内容
   - 补充更多相关文档

---

### Q: 如何查看系统日志？

**A:** 不同组件的日志位置：

```bash
# Docker Compose 部署
docker compose logs                # 所有服务
docker compose logs backend        # 后端日志
docker compose logs frontend       # 前端日志
docker compose logs postgres       # 数据库日志

# 日志级别调整
docker compose exec backend set-log-level DEBUG

# 查看最近 100 行日志并跟踪
docker compose logs -f --tail=100 backend

# 只看错误日志
docker compose logs backend | grep -i error
```

---

## 📞 需要更多帮助？

如果以上 FAQ 没有解决你的问题：

1. **查看文档**：[文档中心](https://docs.beaverchain.ai)
2. **提交 Issue**：[GitHub Issues](https://github.com/vova-byte417/BeaverChain/issues)
3. **联系支持**：support@beaverchain.ai
4. **社区论坛**：[Discord 社区](https://discord.gg/beaverchain)

---

*文档版本: v1.0*
*最后更新: 2026-05-12*
