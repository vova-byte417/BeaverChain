# BeaverChain 文档中心

> 欢迎使用 BeaverChain 大模型构建系统！本文档将帮助你快速上手并深入了解系统的各个功能模块。

---

## 📚 文档索引

### 🚀 入门指南

| 文档 | 描述 | 预计阅读时间 |
|------|------|-------------|
| [快速入门教程](../quickstart.md) | 5 分钟上手核心功能 | ⏱️ 5 分钟 |
| [安装指南](../installation.md) | 详细的安装步骤和环境配置 | ⏱️ 15 分钟 |
| [项目 README](../README.md) | 项目概览和核心特性介绍 | ⏱️ 10 分钟 |

### 👤 用户文档

| 文档 | 描述 | 预计阅读时间 |
|------|------|-------------|
| [用户手册](user/user-guide.md) | 完整功能使用说明 | ⏱️ 30 分钟 |
| [常见问题 FAQ](user/faq.md) | 常见问题解答 | ⏱️ 10 分钟 |
| [最佳实践](user/best-practices.md) | 企业级使用指南 | ⏱️ 20 分钟 |
| [Prompt 工程指南](user/prompt-engineering.md) | Prompt 编写技巧与最佳实践 | ⏱️ 25 分钟 |

### 👨‍💻 开发者文档

| 文档 | 描述 | 预计阅读时间 |
|------|------|-------------|
| [API 参考手册](api/README.md) | REST API 完整文档 | ⏱️ 45 分钟 |
| [Python SDK 文档](api/python-sdk.md) | Python SDK 使用指南 | ⏱️ 30 分钟 |
| [代码结构说明](developer/code-structure.md) | 项目代码架构详解 | ⏱️ 20 分钟 |
| [贡献指南](developer/contributing.md) | 如何参与项目开发 | ⏱️ 15 分钟 |
| [调试技巧](developer/debugging.md) | 问题排查与调试方法 | ⏱️ 20 分钟 |

### 🧪 测试文档

| 文档 | 描述 | 预计阅读时间 |
|------|------|-------------|
| [测试说明](testing.md) | 测试框架介绍与运行指南 | ⏱️ 15 分钟 |
| [E2E 测试用例](developer/e2e-test-cases.md) | 端到端测试场景说明 | ⏱️ 20 分钟 |

### 🚀 部署与运维

| 文档 | 描述 | 预计阅读时间 |
|------|------|-------------|
| [部署文档](deployment.md) | 生产环境部署配置 | ⏱️ 30 分钟 |
| [监控与告警](developer/monitoring.md) | 系统监控指标与告警配置 | ⏱️ 20 分钟 |
| [备份与恢复](developer/backup-restore.md) | 数据备份与灾难恢复 | ⏱️ 15 分钟 |

---

## 🎯 我应该从哪里开始？

### 如果你是第一次使用 BeaverChain

1. **先读 [快速入门教程](../quickstart.md)** - 5 分钟了解核心功能
2. **再读 [安装指南](../installation.md)** - 在你的环境中安装系统
3. **最后读 [用户手册](user/user-guide.md)** - 深入学习所有功能

### 如果你是开发者，想要集成 BeaverChain

1. **先读 [API 参考手册](api/README.md)** - 了解所有 API 端点
2. **再读 [Python SDK 文档](api/python-sdk.md)** - 使用 SDK 快速开发
3. **查看 [代码示例](developer/code-examples.md)** - 丰富的代码示例

### 如果你是 DevOps，想要部署生产环境

1. **先读 [部署文档](deployment.md)** - Kubernetes 和 Docker 部署指南
2. **再读 [监控与告警](developer/monitoring.md)** - 配置监控和告警
3. **最后读 [备份与恢复](developer/backup-restore.md)** - 确保数据安全

---

## 📖 核心功能模块概览

### 1. 🗂️ 模型版本管理
- 完整的模型版本控制（weights, prompt, RAG config, guardrails）
- 版本对比和一键回滚
- 血缘追踪和变更历史

### 2. 📝 Prompt 管理
- 富文本编辑器（变量高亮、语法检查）
- 分支管理和合并
- 版本对比和回滚
- A/B 测试支持

### 3. 🔍 RAG 知识库
- 多种文档格式支持（PDF、Word、Markdown、网页）
- 向量化和相似度检索
- 知识库版本化
- 检索效果评估

### 4. 🛡️ Guardrails 安全
- 毒性过滤和内容安全
- 幻觉检测和防护
- 敏感词管理
- 输出格式验证

### 5. ⚡ 工作流编排
- 拖拽式可视化设计器
- 多种节点类型（LLM、条件、检索、工具等）
- 子工作流嵌套
- 实时执行监控

### 6. 📊 评估监控
- 幻觉率、毒性、忠实度指标
- 性能指标监控（延迟、吞吐量）
- 成本统计和分析
- 智能告警和通知

---

## 🔗 API 快速参考

### 基础信息
- **Base URL**: `http://your-domain.com/api/v1`
- **认证方式**: Bearer Token
- **API 文档**: `http://your-domain.com/docs` (Swagger UI)

### 常用端点

```bash
# 模型版本
GET    /api/v1/model-versions          # 列出版本
POST   /api/v1/model-versions          # 创建版本
GET    /api/v1/model-versions/{id}     # 获取版本详情
PATCH  /api/v1/model-versions/{id}     # 更新版本
DELETE /api/v1/model-versions/{id}     # 删除版本

# 版本管理
GET    /api/v1/model-versions/compare          # 对比版本
POST   /api/v1/model-versions/{id}/rollback    # 回滚版本
GET    /api/v1/model-versions/history/{name}   # 版本历史

# 文件上传
POST   /api/v1/model-versions/upload/simple    # 简单上传
POST   /api/v1/model-versions/upload/init      # 初始化分片上传
POST   /api/v1/model-versions/upload/chunk     # 上传分片
POST   /api/v1/model-versions/upload/complete  # 完成上传

# 健康检查
GET    /health                                  # 服务健康状态
```

详细的 API 文档请参考 [API 参考手册](api/README.md)。

---

## 💡 代码示例

### Python SDK 快速使用

```python
from beaverchain import ModelRegistryClient

# 初始化客户端
client = ModelRegistryClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# 创建模型版本
version = client.create_version({
    "name": "customer-support",
    "version": "1.0.0",
    "status": "production",
    "prompt_config": {
        "template": "你是一个有帮助的助手...",
        "variables": ["user_query"]
    },
    "tags": ["production", "support"]
})

# 查看版本历史
history = client.get_version_history("customer-support")

# 对比版本
diff = client.compare_versions(version_a_id, version_b_id)

# 回滚版本
rolled_back = client.rollback_version(
    version_id=current_version_id,
    target_version_id=previous_version_id,
    reason="性能下降"
)
```

更多示例请参考 [代码示例文档](developer/code-examples.md)。

---

## 🆘 获得帮助

如果你在使用过程中遇到问题，可以通过以下方式获得帮助：

### 1. 查看 FAQ
先查看 [常见问题 FAQ](user/faq.md)，你的问题可能已经有了解答。

### 2. 提交 Issue
如果是 Bug 或功能建议，请在 GitHub 提交 Issue：
https://github.com/vova-byte417/BeaverChain/issues

### 3. 联系支持
- **邮件**: support@beaverchain.ai
- **社区论坛**: https://community.beaverchain.ai
- **企业支持**: 企业版用户可通过专属渠道获取支持

---

## 📅 版本信息

| 项目 | 信息 |
|------|------|
| **当前版本** | v1.0.0-alpha |
| **发布日期** | 2026-05-12 |
| **文档更新** | 2026-05-12 |
| **兼容性** | Python 3.10+, Node.js 18+, PostgreSQL 15+ |

---

## 🔄 更新日志

### v1.0.0-alpha (2026-05-12)
- ✨ 初始版本发布
- 📦 核心版本控制功能
- 📝 Prompt 管理模块
- 🔍 RAG 知识库支持
- 🛡️ Guardrails 安全护栏
- ⚡ 工作流编排引擎
- 📊 评估监控面板
- 🌐 Web Dashboard 前端
- 📚 完整的文档体系

---

## 🤝 参与贡献

我们欢迎所有形式的贡献！包括但不限于：

- 🐛 报告 Bug
- ✨ 提出新功能建议
- 📝 改进文档
- 💻 提交代码修复或新功能
- 🌐 翻译和本地化

请阅读 [贡献指南](developer/contributing.md) 了解如何参与。

---

## 📄 许可证

本项目采用 MIT 许可证。

---

**祝您使用愉快！** 🎉

> BeaverChain 团队
> 2026-05-12

---

*如有任何问题或建议，欢迎随时联系我们！*
