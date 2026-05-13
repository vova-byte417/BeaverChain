"""
Model Registry - 模型版本化核心服务
主应用入口文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
import os

from .api.routes import router as model_registry_router
from .services.database import DatabaseService

# 应用信息
APP_NAME = os.environ.get("APP_NAME", "Model Registry")
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
大模型构建系统 - 模型版本化核心模块

提供以下功能：
- 📦 模型权重版本化管理
- 💬 Prompt / System Prompt 版本管理
- 🔍 RAG 配置版本管理
- 🛡️ Guardrails 安全配置版本管理
- 🧪 评估指标存储与对比
- ⏪ 一键回滚到任意历史版本
- 📊 版本差异对比
- 💾 本地文件系统 / S3 兼容对象存储支持
- 📁 大文件分片上传支持
"""

# 创建 FastAPI 应用
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "BeaverChain Team",
        "url": "https://github.com/beaverchain",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 根路由 - 重定向到文档
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# 健康检查
@app.get("/health", summary="健康检查", tags=["System"])
async def health_check():
    """服务健康检查端点"""
    return {
        "status": "healthy",
        "service": "Model Registry",
        "version": APP_VERSION
    }


# 数据库初始化检查
@app.get("/health/db", summary="数据库健康检查", tags=["System"])
async def db_health_check():
    """数据库连接健康检查"""
    try:
        db = DatabaseService()
        stats = db.get_statistics()
        return {
            "status": "healthy",
            "database": "connected",
            "statistics": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# 注册 API 路由
app.include_router(model_registry_router)


def create_tables(database_url: str = None):
    """
    创建数据库表
    
    Args:
        database_url: 数据库连接 URL，默认为 sqlite:///./model_registry.db
    """
    if not database_url:
        database_url = os.environ.get(
            "DATABASE_URL",
            "sqlite:///./model_registry.db"
        )
    
    db = DatabaseService(database_url)
    print(f"✓ Database tables created successfully using {database_url}")
    return db


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = True,
    workers: int = 1
):
    """
    启动 API 服务器
    
    Args:
        host: 监听地址
        port: 监听端口
        reload: 是否自动重载（开发模式）
        workers: Worker 进程数
    """
    print(f"🚀 Starting Model Registry Server v{APP_VERSION}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"📖 Redoc: http://{host}:{port}/redoc")
    print("-" * 50)
    
    uvicorn.run(
        "model_registry.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers
    )


if __name__ == "__main__":
    # 创建数据库表
    create_tables()
    
    # 启动服务器
    run_server()
