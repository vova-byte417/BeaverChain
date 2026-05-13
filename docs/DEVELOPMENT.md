# 开发规范

本文档定义了 BeaverChain 项目的开发规范和最佳实践，所有贡献者都必须遵守。

## 📋 目录

- [代码规范](#代码规范)
- [Git 工作流](#git-工作流)
- [分支管理](#分支管理)
- [提交规范](#提交规范)
- [代码审查](#代码审查)
- [测试规范](#测试规范)
- [文档规范](#文档规范)
- [安全规范](#安全规范)
- [性能优化指南](#性能优化指南)

## 代码规范

### Python 代码规范

#### 基础规范

- 遵循 **PEP 8** 规范
- 使用 **Black** 进行代码格式化
- 使用 **isort** 进行 import 排序
- 使用 **flake8** 进行代码检查
- 使用 **mypy** 进行类型检查

#### 配置文件

```ini
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py310']

[tool.isort]
profile = "black"
line-length = 100
multi_line_output = 3

[tool.mypy]
python_version = "3.10"
strict = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
addopts = "-v --cov=core --cov-report=term --cov-report=html"
testpaths = ["tests"]
python_files = ["test_*.py"]
```

#### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块名 | 小写 + 下划线 | `model_registry`, `quantization` |
| 类名 | 大驼峰 (PascalCase) | `ModelRegistry`, `Quantizer` |
| 函数名 | 小写 + 下划线 (snake_case) | `get_model()`, `quantize_model()` |
| 变量名 | 小写 + 下划线 | `model_id`, `batch_size` |
| 常量名 | 全大写 + 下划线 | `MAX_BATCH_SIZE`, `DEFAULT_TIMEOUT` |
| 私有成员 | 前缀下划线 | `_internal_method()`, `_cache` |

#### 类型注解示例

```python
from typing import List, Dict, Optional, Union, Any, Literal
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    """模型配置数据类"""
    model_id: str = Field(..., description="模型唯一标识")
    name: str = Field(..., description="模型名称")
    max_tokens: int = Field(default=4096, ge=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    device: Literal["cpu", "cuda", "auto"] = "auto"

class ModelRegistry:
    """模型注册器"""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self._models: Dict[str, Any] = {}

    def register(self, model_id: str, model: Any) -> bool:
        """
        注册模型

        Args:
            model_id: 模型唯一标识
            model: 模型实例

        Returns:
            注册成功返回 True，失败返回 False

        Raises:
            ValueError: 当 model_id 已存在时
        """
        if model_id in self._models:
            raise ValueError(f"Model {model_id} already exists")

        self._models[model_id] = model
        return True

    def get(self, model_id: str) -> Optional[Any]:
        """获取模型"""
        return self._models.get(model_id)

    def list_models(self) -> List[str]:
        """列出所有模型 ID"""
        return list(self._models.keys())
```

#### 文档字符串规范

使用 Google 风格的 docstring：

```python
def process_batch(
    batch: List[Dict[str, Any]],
    max_retries: int = 3,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    批量处理模型推理请求

    Args:
        batch: 请求批次，每个元素是包含 prompt 和参数的字典
        max_retries: 最大重试次数，默认为 3
        timeout: 超时时间（秒），默认为 30.0

    Returns:
        处理结果字典，包含：
        - success: 成功处理的数量
        - failed: 失败处理的数量
        - results: 详细结果列表

    Raises:
        TimeoutError: 处理超时时抛出
        RuntimeError: 处理失败时抛出

    Example:
        >>> batch = [{"prompt": "Hello"}, {"prompt": "World"}]
        >>> result = process_batch(batch)
        >>> result["success"]
        2
    """
    pass
```

### TypeScript/React 代码规范

#### ESLint 配置

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended"
  ],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "@typescript-eslint/explicit-function-return-type": "error",
    "@typescript-eslint/no-explicit-any": "warn",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

#### 组件命名规范

- 组件文件：PascalCase (`ModelCard.tsx`)
- 组件名：PascalCase (`ModelCard`)
- Hook：`use` 前缀 (`useModelQuery`)
- 工具函数：camelCase (`formatDate`)

#### React 组件最佳实践

```tsx
import { useQuery } from '@tanstack/react-query';
import { Card, Badge, Skeleton } from '@/components/ui';
import { cn } from '@/utils/cn';

interface ModelCardProps {
  /** 模型 ID */
  modelId: string;
  /** 是否显示详细信息 */
  showDetails?: boolean;
  /** 自定义类名 */
  className?: string;
}

interface ModelData {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'deploying';
  metrics: {
    latency: number;
    throughput: number;
  };
}

/**
 * 模型卡片组件
 * 显示模型的基本信息和运行指标
 */
export function ModelCard({
  modelId,
  showDetails = false,
  className
}: ModelCardProps): JSX.Element {
  const { data, isLoading, error } = useQuery<ModelData>({
    queryKey: ['models', modelId],
    queryFn: () => fetch(`/api/v1/models/${modelId}`).then(res => res.json()),
    staleTime: 5 * 60 * 1000, // 5 分钟缓存
  });

  if (isLoading) {
    return <Skeleton className={cn('h-48 w-full', className)} />;
  }

  if (error || !data) {
    return (
      <Card className={cn('border-red-200 bg-red-50', className)}>
        <p className="text-red-600">加载失败</p>
      </Card>
    );
  }

  const statusColors = {
    active: 'bg-green-100 text-green-800',
    inactive: 'bg-gray-100 text-gray-800',
    deploying: 'bg-blue-100 text-blue-800'
  };

  return (
    <Card className={cn('p-4 hover:shadow-lg transition-shadow', className)}>
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold">{data.name}</h3>
        <Badge className={statusColors[data.status]}>
          {data.status}
        </Badge>
      </div>

      {showDetails && (
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>延迟</span>
            <span>{data.metrics.latency}ms</span>
          </div>
          <div className="flex justify-between">
            <span>吞吐量</span>
            <span>{data.metrics.throughput} token/s</span>
          </div>
        </div>
      )}
    </Card>
  );
}

export default ModelCard;
```

## Git 工作流

### 分支管理策略

我们采用 **Git Flow** 工作流的简化版本：

```
main (生产环境)
  ↑
staging (预发布环境)
  ↑
develop (开发环境)
  ↑
feature/xxx (功能分支)
bugfix/xxx (修复分支)
hotfix/xxx (紧急修复分支)
```

#### 分支说明

| 分支 | 说明 | 命名规范 |
|------|------|---------|
| `main` | 生产环境分支，稳定可发布 | - |
| `staging` | 预发布环境，用于集成测试 | - |
| `develop` | 开发分支，最新代码 | - |
| `feature/*` | 功能开发分支 | `feature/功能描述` |
| `bugfix/*` | Bug 修复分支 | `bugfix/问题描述` |
| `hotfix/*` | 紧急修复分支 | `hotfix/问题描述` |
| `release/*` | 发布准备分支 | `release/v1.2.3` |

### 开发流程

#### 1. 创建功能分支

```bash
# 从 develop 创建新分支
git checkout develop
git pull origin develop
git checkout -b feature/user-authentication
```

#### 2. 开发并提交代码

```bash
# 开发...
git add .
git commit -m "feat: add user authentication with JWT"

# 推送分支
git push origin feature/user-authentication
```

#### 3. 创建 Pull Request

在 GitHub 上创建 PR：
- Source: `feature/user-authentication`
- Target: `develop`
- 填写 PR 模板，包含：
  - 功能描述
  - 实现方案
  - 测试覆盖情况
  - 截图（如涉及 UI）

#### 4. 代码审查

- 至少需要 1 名 Reviewer 批准
- 所有 CI 检查必须通过
- 解决所有 Review Comments

#### 5. 合并到 develop

```bash
# Squash Merge（推荐）
# 或 Rebase Merge
```

### 发布流程

```bash
# 1. 创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# 2. 更新版本号
# 修改 package.json, version.py 等

# 3. 更新 CHANGELOG.md

# 4. 提交并推送
git add .
git commit -m "chore: release v1.2.0"
git push origin release/v1.2.0

# 5. 合并到 main 和 develop
git checkout main
git merge release/v1.2.0 --no-ff
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags

git checkout develop
git merge release/v1.2.0 --no-ff
git push origin develop

# 6. 删除发布分支
git branch -d release/v1.2.0
git push origin --delete release/v1.2.0
```

## 提交规范

### Conventional Commits

所有 Git Commit 必须遵循 **Conventional Commits** 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### 类型 (type)

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响代码运行） |
| `refactor` | 重构（既不是新增功能，也不是修复bug） |
| `perf` | 性能优化 |
| `test` | 增加测试或修改测试 |
| `chore` | 构建过程或辅助工具的变动 |
| `ci` | CI/CD 相关变更 |
| `revert` | 回滚某次提交 |

### 作用域 (scope) 可选

表示变更影响的范围，例如：
- `api` - API 层
- `model` - 模型相关
- `frontend` - 前端
- `db` - 数据库
- `quant` - 量化模块
- `deploy` - 部署模块

### 描述 (description)

- 使用祈使句（"add" 而非 "added" 或 "adds"）
- 首字母小写
- 结尾不使用句号
- 长度不超过 72 字符

### 提交示例

```bash
# 新功能
git commit -m "feat(auth): add JWT authentication middleware"

# Bug 修复
git commit -m "fix(api): resolve race condition in batch processing"

# 文档更新
git commit -m "docs: add API documentation for model registry"

# 重构
git commit -m "refactor(quant): simplify AWQ quantization logic"

# 性能优化
git commit -m "perf(inference): reduce GPU memory usage by 30%"

# 测试
git commit -m "test: add integration tests for deployment API"

# 构建相关
git commit -m "chore: update dependencies to latest versions"
```

### 破坏性变更

如果提交包含破坏性变更，需要在 Footer 标注 `BREAKING CHANGE`：

```
feat(api): update deployment API to v2

BREAKING CHANGE: The deployment API endpoints have changed.
Old endpoints are deprecated and will be removed in v2.0.

Migration guide:
- /api/v1/deploy -> /api/v2/deployments
- Request body format changed
```

## 代码审查

### Reviewer 检查清单

在批准 PR 之前，请检查以下项目：

#### 功能正确性
- [ ] 代码逻辑是否正确实现需求？
- [ ] 是否处理了边界情况？
- [ ] 是否存在潜在的并发问题？
- [ ] 错误处理是否完善？

#### 代码质量
- [ ] 命名是否清晰且符合规范？
- [ ] 函数/类是否过大（超过 200 行）？
- [ ] 是否存在重复代码？
- [ ] 注释是否充分且不过度？
- [ ] 是否有魔法数字需要提取为常量？

#### 性能考虑
- [ ] 算法复杂度是否合理（O(n²) 以上需要说明）？
- [ ] 是否存在内存泄漏风险？
- [ ] 数据库查询是否需要索引？
- [ ] 是否有 N+1 查询问题？

#### 安全性
- [ ] 用户输入是否做了验证和清理？
- [ ] SQL 注入防护是否到位？
- [ ] XSS 攻击防护是否考虑？
- [ ] 敏感信息是否没有硬编码？
- [ ] 权限检查是否完整？

#### 测试覆盖
- [ ] 单元测试是否覆盖了主要逻辑？
- [ ] 边界情况是否有测试用例？
- [ ] 集成测试是否通过？
- [ ] 测试是否稳定（不依赖外部服务）？

#### 文档
- [ ] 新增功能是否更新了相关文档？
- [ ] API 文档是否同步更新？
- [ ] README 是否需要更新？

### Review 反馈规范

#### 使用代码建议

```markdown
建议简化这段逻辑：

```suggestion
result = [item for item in items if item.valid]
```

原代码虽然正确，但列表推导更简洁高效。
```

#### 分级反馈

- **🔴 必须修改**：Bug、安全问题、性能问题
- **🟡 建议修改**：代码质量、可读性、可维护性
- **🟢 可选优化**：风格偏好、小改进

### 作者回应规范

- 所有评论必须回应（解决或解释不解决的原因）
- 解决的评论点击 "Resolve"
- 有分歧的评论邀请讨论，不要直接忽略

## 测试规范

### 测试金字塔

```
        /\
       /  \    E2E 测试 (少量)
      /____\
     /      \  集成测试 (适量)
    /________\
   /          \ 单元测试 (大量)
  /____________\
```

### 单元测试规范

#### 测试文件组织

```
tests/
├── unit/
│   ├── test_model_registry.py
│   ├── test_quantization.py
│   └── test_deployment.py
├── integration/
│   ├── test_api_endpoints.py
│   └── test_database.py
└── e2e/
    └── test_full_workflow.py
```

#### 单元测试示例

```python
import pytest
from unittest.mock import Mock, patch, MagicMock

from core.model_registry import ModelRegistry
from core.exceptions import ModelNotFoundError


class TestModelRegistry:
    """模型注册器测试套件"""

    def setup_method(self):
        """每个测试前的准备工作"""
        self.registry = ModelRegistry()
        self.test_model = Mock()
        self.test_model_id = "test-model-123"

    def test_register_model_success(self):
        """测试成功注册模型"""
        # Act
        result = self.registry.register(self.test_model_id, self.test_model)

        # Assert
        assert result is True
        assert self.registry.get(self.test_model_id) == self.test_model

    def test_register_duplicate_model_raises_error(self):
        """测试重复注册模型应该抛出异常"""
        # Arrange
        self.registry.register(self.test_model_id, self.test_model)

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            self.registry.register(self.test_model_id, Mock())

    def test_get_nonexistent_model_returns_none(self):
        """测试获取不存在的模型返回 None"""
        # Act
        result = self.registry.get("nonexistent-model")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_async_model_loading(self):
        """测试异步模型加载"""
        # Arrange
        mock_loader = Mock()
        mock_loader.load.return_value = self.test_model

        # Act
        result = await self.registry.load_async(
            model_id=self.test_model_id,
            loader=mock_loader
        )

        # Assert
        assert result == self.test_model
        mock_loader.load.assert_called_once_with(self.test_model_id)

    @patch('core.model_registry.os.path.exists')
    def test_load_from_disk(self, mock_exists):
        """测试从磁盘加载模型（使用 mock）"""
        # Arrange
        mock_exists.return_value = True

        # Act
        model = self.registry.load_from_disk("/path/to/model")

        # Assert
        assert model is not None
        mock_exists.assert_called_once_with("/path/to/model")


class TestModelRegistryEdgeCases:
    """边界情况测试"""

    def test_empty_model_id_rejected(self):
        """测试空模型 ID 被拒绝"""
        registry = ModelRegistry()

        with pytest.raises(ValueError, match="model_id cannot be empty"):
            registry.register("", Mock())

    def test_none_model_rejected(self):
        """测试 None 模型被拒绝"""
        registry = ModelRegistry()

        with pytest.raises(ValueError, match="model cannot be None"):
            registry.register("test-id", None)
```

### 测试 Fixture

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from core.database import Base, get_db

# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    """数据库引擎 Fixture"""
    return create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    """创建测试 Session"""
    Base.metadata.create_all(bind=test_engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session(TestingSessionLocal):
    """数据库会话 Fixture"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """API 测试客户端 Fixture"""
    # 覆盖依赖
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # 清理
    del app.dependency_overrides[get_db]
```

### 测试覆盖率要求

| 模块 | 最低覆盖率 |
|------|-----------|
| 核心业务逻辑 | ≥ 90% |
| API 层 | ≥ 80% |
| 工具类 | ≥ 95% |
| 配置和脚本 | ≥ 50% |

## 文档规范

### 代码内文档

- 所有公开的类、方法、函数都必须有文档字符串
- 复杂的算法必须添加行内注释解释逻辑
- 业务规则的实现必须说明为什么这么做
- 修复 Bug 的代码必须注释 Bug 链接或说明

### API 文档

所有 API 端点必须包含：

```python
@app.post("/api/v1/models/{model_id}/deploy", response_model=DeploymentResponse)
async def deploy_model(
    model_id: str = Path(..., description="要部署的模型 ID"),
    config: DeploymentConfig = Body(..., description="部署配置"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    部署模型

    此端点用于将已注册的模型部署到推理集群。部署完成后，
    可以通过返回的端点进行模型推理。

    Args:
        model_id: 要部署的模型唯一标识
        config: 部署配置参数，包括 GPU 数量、引擎类型等
        current_user: 当前认证用户（自动注入）

    Returns:
        DeploymentResponse: 包含部署 ID、端点 URL、状态等信息

    Raises:
        ModelNotFoundError: 当 model_id 不存在时
        PermissionDeniedError: 当用户无部署权限时
        InsufficientResourcesError: 当 GPU 资源不足时

    Example:
        curl -X POST "http://api.example.com/v1/models/llama2-7b/deploy" \
             -H "Authorization: Bearer <token>" \
             -H "Content-Type: application/json" \
             -d '{"gpu_count": 1, "engine": "vllm"}'
    """
    pass
```

### README 标准

每个子项目都应该包含：

```markdown
# 项目名称

简短描述

## 功能特性

- ✨ 特性 1
- 🚀 特性 2
- 🛡️ 特性 3

## 快速开始

### 前置条件

列出运行所需的软件环境

### 安装

详细的安装步骤

### 使用示例

```python
# 代码示例
```

## 开发

### 本地开发

```bash
# 步骤说明
```

### 运行测试

```bash
pytest
```

## 贡献指南

请阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)

## 许可证

MIT License
```

## 安全规范

### 代码安全检查清单

- [ ] 不硬编码密码、API Key、Token 等敏感信息
- [ ] 使用环境变量或密钥管理服务存储机密
- [ ] 所有用户输入都经过验证（长度、格式、范围）
- [ ] 使用参数化查询防止 SQL 注入
- [ ] 输出内容进行适当的转义防止 XSS
- [ ] 文件上传验证类型、大小、内容
- [ ] 路径使用白名单验证，防止路径遍历
- [ ] 身份认证机制使用成熟库，不自行实现
- [ ] 密码使用 bcrypt/Argon2 等强哈希算法
- [ ] JWT 使用安全配置（短过期时间、刷新机制）
- [ ] 权限检查粒度到操作级别，不只是模块级别
- [ ] 错误信息不暴露系统内部细节
- [ ] 日志不记录敏感信息

### 依赖安全

```bash
# 使用 safety 检查依赖漏洞
pip install safety
safety check

# 使用 pip-audit
pip install pip-audit
pip-audit

# npm 依赖检查
npm audit
npm audit fix
```

### 敏感信息检查

```bash
# 安装 gitleaks
brew install gitleaks  # macOS
# or
docker pull zricethezav/gitleaks

# 运行检查
gitleaks detect --source .
```

## 性能优化指南

### 数据库优化

#### 索引优化

```python
# 在模型定义中添加索引
class Model(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 复合索引
    __table_args__ = (
        Index('idx_model_status_created', 'status', 'created_at'),
    )
```

#### 查询优化

```python
# ❌ 不好的做法 - N+1 查询
for model in models:
    deployments = session.query(Deployment).filter_by(model_id=model.id).all()

# ✅ 好的做法 - 预加载 + 批量查询
from sqlalchemy.orm import joinedload

models = session.query(Model).options(
    joinedload(Model.deployments)
).all()
```

### 缓存策略

```python
from functools import lru_cache
import redis

# 内存缓存（适合小数据、高访问频率）
@lru_cache(maxsize=1000)
def get_model_config(model_id: str):
    """获取模型配置（带缓存）"""
    return db.query(ModelConfig).filter_by(model_id=model_id).first()


# Redis 分布式缓存（适合跨进程、跨机器）
class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    def get(self, key: str):
        value = self.redis.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, ttl: int = 3600):
        self.redis.setex(key, ttl, json.dumps(value))
```

### 异步编程最佳实践

```python
# ✅ 正确 - 使用异步驱动
async def get_model(model_id: str):
    return await db.fetch_one(
        "SELECT * FROM models WHERE id = :id",
        {"id": model_id}
    )

# ❌ 错误 - 在异步函数中做阻塞 IO
async def bad_example():
    # 这会阻塞整个事件循环
    response = requests.get("https://api.example.com")
    return response.json()

# ✅ 正确 - 使用异步 HTTP 客户端
async def good_example():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()
```

---

## 📚 参考资料

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [React Documentation](https://react.dev/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

**文档版本**: v1.0.0  
**最后更新**: 2024-05-13
