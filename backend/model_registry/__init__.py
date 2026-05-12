"""
Model Registry - 模型版本化核心模块
========================================

大模型构建系统（BeaverChain）的核心版本管理模块。

功能特性:
    - 📦 完整的模型版本管理（权重 / Prompt / RAG / Guardrails / 推理参数）
    - 📜 完整的版本历史和血缘追踪
    - 🔍 版本差异对比
    - ⏪ 一键回滚到任意历史版本
    - 💾 本地文件系统 / S3 兼容对象存储支持
    - 📁 大文件分片上传（支持 GB 级模型文件）
    - 🌐 RESTful API + OpenAPI 文档
    - 🐍 Python SDK / CLI 支持

模块结构:
    model_registry/
    ├── __init__.py          # 本文件
    ├── main.py              # FastAPI 应用入口
    ├── requirements.txt     # 依赖列表
    ├── models/              # 数据模型定义
    │   ├── __init__.py
    │   └── schemas.py       # Pydantic Schema + SQLAlchemy ORM
    ├── services/            # 业务服务层
    │   ├── __init__.py
    │   ├── database.py      # 数据库服务
    │   └── storage.py       # 存储服务（本地 / S3）
    ├── api/                 # API 层
    │   ├── __init__.py
    │   └── routes.py        # FastAPI 路由
    ├── tests/               # 单元测试
    │   ├── __init__.py
    │   ├── test_database.py
    │   ├── test_storage.py
    │   └── test_api.py
    └── examples/            # 使用示例
        ├── __init__.py
        ├── sdk_usage.py     # SDK 示例
        └── cli_tool.py      # CLI 工具示例

快速开始:
    1. 安装依赖: pip install -r requirements.txt
    2. 启动服务: python -m model_registry.main
    3. 访问文档: http://localhost:8000/docs
"""

__version__ = "1.0.0"
__author__ = "BeaverChain Team"
__description__ = "大模型构建系统 - 模型版本化核心模块"

# 导出主要类，方便外部使用
from .services.database import DatabaseService
from .services.storage import StorageService, LocalStorageBackend, S3StorageBackend

__all__ = [
    "DatabaseService",
    "StorageService",
    "LocalStorageBackend",
    "S3StorageBackend",
]
