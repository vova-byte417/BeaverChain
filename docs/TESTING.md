# 测试手册

本文档详细说明了 BeaverChain 项目的测试策略、测试类型、测试工具和最佳实践。

## 📋 目录

- [测试策略](#测试策略)
- [测试类型](#测试类型)
- [测试工具](#测试工具)
- [单元测试指南](#单元测试指南)
- [集成测试指南](#集成测试指南)
- [端到端测试指南](#端到端测试指南)
- [性能测试指南](#性能测试指南)
- [测试数据管理](#测试数据管理)
- [CI/CD 集成](#cicd-集成)
- [最佳实践](#最佳实践)

## 测试策略

### 测试金字塔

```
        /\
       /  \    E2E 测试 (10%)
      /____\
     /      \  集成测试 (30%)
    /________\
   /          \ 单元测试 (60%)
  /____________\
```

### 测试覆盖率目标

| 测试类型 | 覆盖率目标 | 说明 |
|---------|-----------|------|
| 单元测试 | ≥ 90% | 核心业务逻辑必须 100% 覆盖 |
| 集成测试 | ≥ 80% | API 端点和外部集成 |
| E2E 测试 | ≥ 50% | 关键用户流程 |

### 测试执行时机

| 测试类型 | 执行时机 | 责任人 |
|---------|---------|-------|
| 单元测试 | 每次提交、PR 创建时 | 开发人员 |
| 集成测试 | PR 创建时、每日构建 | 开发人员 + QA |
| E2E 测试 | 每日构建、发布前 | QA |
| 性能测试 | 每周、发布候选版本 | DevOps + QA |
| 安全测试 | 每周、发布候选版本 | 安全团队 |

## 测试类型

### 1. 单元测试 (Unit Testing)

**目标**：验证单个组件、类、函数的正确性

**范围**：
- 独立的函数和方法
- 单个类的行为
- 工具类和辅助函数
- 数据验证逻辑

**特点**：
- 快速执行（毫秒级）
- 不依赖外部服务
- 完全可控的输入和输出
- 易于调试和定位问题

### 2. 集成测试 (Integration Testing)

**目标**：验证组件之间的交互是否正确

**范围**：
- API 端点测试
- 数据库操作测试
- 外部服务集成测试
- 组件间接口测试

**特点**：
- 需要测试环境
- 可能依赖数据库、缓存等服务
- 验证数据流和状态转换

### 3. 端到端测试 (End-to-End Testing)

**目标**：模拟真实用户场景，验证整个系统的功能

**范围**：
- 完整的用户工作流程
- 跨系统交互
- UI 交互测试
- 真实数据流程

**特点**：
- 最接近真实使用场景
- 执行时间较长
- 需要完整的测试环境

### 4. 性能测试 (Performance Testing)

**目标**：验证系统在负载下的表现

**类型**：
- 负载测试（Load Testing）
- 压力测试（Stress Testing）
- 容量测试（Capacity Testing）
- 基准测试（Benchmark Testing）

### 5. 安全测试 (Security Testing)

**目标**：发现系统的安全漏洞

**包括**：
- 渗透测试
- 漏洞扫描
- 代码安全审计
- 依赖安全检查

## 测试工具

### Python 后端测试工具

| 工具 | 用途 | 配置 |
|------|------|------|
| `pytest` | 测试框架和运行器 | ✅ 已配置 |
| `pytest-cov` | 覆盖率报告 | ✅ 已配置 |
| `pytest-asyncio` | 异步代码测试 | ✅ 已配置 |
| `pytest-mock` | Mock 支持 | ✅ 已配置 |
| `unittest.mock` | 标准库 Mock | ✅ 内置 |
| `Hypothesis` | 基于属性的测试 | 📌 可选 |
| `Testcontainers` | 容器化测试依赖 | 📌 可选 |

### 前端测试工具

| 工具 | 用途 | 配置 |
|------|------|------|
| `Vitest` | 测试框架和运行器 | ✅ 已配置 |
| `@testing-library/react` | React 组件测试 | ✅ 已配置 |
| `@testing-library/user-event` | 用户交互模拟 | ✅ 已配置 |
| `Playwright` | E2E 和浏览器测试 | 📌 可选 |
| `Cypress` | E2E 测试框架 | 📌 可选 |

### 性能测试工具

| 工具 | 用途 |
|------|------|
| `locust` | Python 负载测试 |
| `k6` | 现代负载测试工具 |
| `wrk` | HTTP 基准测试 |
| `cProfile` | Python 性能分析 |

## 单元测试指南

### 测试文件组织

```
backend/
├── core/
│   ├── model_registry.py
│   └── quantization.py
└── tests/
    └── unit/
        ├── __init__.py
        ├── test_model_registry.py
        └── test_quantization.py
```

### 基础测试结构

```python
# test_model_registry.py
import pytest
from unittest.mock import Mock, patch

from core.model_registry import ModelRegistry
from core.exceptions import ModelNotFoundError


class TestModelRegistry:
    """
    模型注册器测试套件

    测试所有与模型注册、查询、删除相关的功能
    """

    def setup_method(self):
        """每个测试执行前的准备工作"""
        # 创建新的注册器实例
        self.registry = ModelRegistry()
        # 创建测试用的 Mock 模型
        self.mock_model = Mock()
        self.test_model_id = "test-model-123"

    def teardown_method(self):
        """每个测试执行后的清理工作"""
        pass  # 如果需要清理资源，在这里实现

    def test_register_model_successfully(self):
        """测试：成功注册新模型"""
        # Act
        result = self.registry.register(self.test_model_id, self.mock_model)

        # Assert
        assert result is True
        assert self.registry.get(self.test_model_id) == self.mock_model

    def test_register_duplicate_model_raises_error(self):
        """测试：重复注册相同模型 ID 应该抛出异常"""
        # Arrange
        self.registry.register(self.test_model_id, self.mock_model)

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            self.registry.register(self.test_model_id, Mock())

    def test_get_nonexistent_model_returns_none(self):
        """测试：获取不存在的模型返回 None"""
        # Act
        result = self.registry.get("nonexistent-model")

        # Assert
        assert result is None

    def test_list_models_returns_all_registered(self):
        """测试：列出所有已注册的模型"""
        # Arrange
        model_ids = ["model-1", "model-2", "model-3"]
        for mid in model_ids:
            self.registry.register(mid, Mock())

        # Act
        result = self.registry.list_models()

        # Assert
        assert len(result) == 3
        assert set(result) == set(model_ids)

    @pytest.mark.parametrize(
        "model_id, expected_valid",
        [
            ("valid-model", True),
            ("valid_model_123", True),
            ("", False),
            (None, False),
            ("a" * 256, False),  # 过长
            ("invalid/../path", False),  # 路径遍历
        ],
    )
    def test_model_id_validation(self, model_id, expected_valid):
        """测试：模型 ID 格式验证"""
        # Act
        is_valid = self.registry.validate_model_id(model_id)

        # Assert
        assert is_valid == expected_valid
```

### 使用 Fixture

```python
# conftest.py
import pytest
from unittest.mock import Mock

from core.model_registry import ModelRegistry


@pytest.fixture
def empty_registry():
    """创建空的模型注册器"""
    return ModelRegistry()


@pytest.fixture
def populated_registry():
    """创建包含测试数据的模型注册器"""
    registry = ModelRegistry()

    # 添加几个测试模型
    for i in range(3):
        registry.register(f"model-{i}", Mock(name=f"Model {i}"))

    return registry


@pytest.fixture
def mock_model():
    """创建一个 Mock 模型"""
    model = Mock()
    model.name = "Test Model"
    model.version = "1.0.0"
    return model
```

### Mock 外部依赖

```python
from unittest.mock import patch, MagicMock


class TestModelDeployment:
    """模型部署测试"""

    @patch('core.deployment.docker_client')
    def test_deploy_model_creates_container(self, mock_docker_client):
        """测试：部署模型时正确创建 Docker 容器"""
        # Arrange
        mock_container = Mock()
        mock_container.id = "container-123"
        mock_docker_client.containers.create.return_value = mock_container

        deployer = ModelDeployer()

        # Act
        deployment_id = deployer.deploy("model-1", gpu_count=1)

        # Assert
        assert deployment_id == "container-123"
        mock_docker_client.containers.create.assert_called_once()

    @patch('core.deployment.requests.post')
    def test_health_check_handles_timeout(self, mock_post):
        """测试：健康检查超时处理"""
        # Arrange
        mock_post.side_effect = TimeoutError("Connection timed out")

        deployer = ModelDeployer()

        # Act
        is_healthy = deployer.check_health("http://model-endpoint/health")

        # Assert
        assert is_healthy is False
```

### 测试异常情况

```python
import pytest


class TestErrorHandling:
    """错误处理测试"""

    def test_model_not_found_exception(self, empty_registry):
        """测试：查询不存在的模型抛出正确异常"""
        # Act & Assert
        with pytest.raises(ModelNotFoundError) as exc_info:
            empty_registry.get_or_raise("nonexistent-model")

        assert "nonexistent-model" in str(exc_info.value)

    def test_timeout_error_retries(self):
        """测试：超时后自动重试"""
        # Arrange
        service = ReliableService()
        call_count = 0

        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Temporary failure")
            return "success"

        service.operation = flaky_operation

        # Act
        result = service.execute_with_retry(max_retries=3)

        # Assert
        assert result == "success"
        assert call_count == 3
```

## 集成测试指南

### API 端点测试

```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from core.database import Base, get_db


# 使用内存 SQLite 进行集成测试
TEST_DATABASE_URL = "sqlite:///./test_integration.db"


@pytest.fixture(scope="module")
def test_engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine):
    """创建数据库会话"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """创建 API 测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


class TestModelAPI:
    """模型管理 API 集成测试"""

    def test_create_model(self, client):
        """测试：创建模型 API"""
        # Arrange
        payload = {
            "name": "test-model",
            "type": "llm",
            "source": "huggingface",
            "path": "org/test-model",
        }

        # Act
        response = client.post("/api/v1/models", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-model"
        assert "id" in data

    def test_get_model(self, client):
        """测试：获取模型详情 API"""
        # 首先创建模型
        create_response = client.post(
            "/api/v1/models",
            json={"name": "get-test-model", "type": "llm", "source": "local", "path": "/local"}
        )
        model_id = create_response.json()["id"]

        # Act
        response = client.get(f"/api/v1/models/{model_id}")

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "get-test-model"

    def test_list_models_with_pagination(self, client):
        """测试：模型列表分页"""
        # Arrange - 创建多个模型
        for i in range(15):
            client.post(
                "/api/v1/models",
                json={"name": f"model-{i}", "type": "llm", "source": "local", "path": f"/path/{i}"}
            )

        # Act
        response = client.get("/api/v1/models?page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] >= 15
        assert data["page"] == 1

    def test_update_model_status(self, client):
        """测试：更新模型状态"""
        # Arrange
        create_response = client.post(
            "/api/v1/models",
            json={"name": "update-test", "type": "llm", "source": "local", "path": "/path"}
        )
        model_id = create_response.json()["id"]

        # Act
        response = client.patch(
            f"/api/v1/models/{model_id}",
            json={"status": "active"}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_delete_model(self, client):
        """测试：删除模型"""
        # Arrange
        create_response = client.post(
            "/api/v1/models",
            json={"name": "delete-test", "type": "llm", "source": "local", "path": "/path"}
        )
        model_id = create_response.json()["id"]

        # Act
        response = client.delete(f"/api/v1/models/{model_id}")

        # Assert
        assert response.status_code == 204

        # 验证已删除
        get_response = client.get(f"/api/v1/models/{model_id}")
        assert get_response.status_code == 404
```

### 数据库集成测试

```python
# tests/integration/test_database.py
import pytest
from sqlalchemy import text

from core.models import Model, Deployment
from core.database import SessionLocal


class TestDatabaseOperations:
    """数据库操作集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        """每个测试前设置"""
        self.db = db_session
        # 清理测试数据
        self.db.query(Deployment).delete()
        self.db.query(Model).delete()
        self.db.commit()

    def test_create_and_query_model(self):
        """测试：创建和查询模型记录"""
        # Arrange
        model = Model(
            id="test-model-001",
            name="Test Model",
            type="llm",
            source="huggingface",
            path="org/model",
            status="inactive"
        )

        # Act
        self.db.add(model)
        self.db.commit()

        # Assert
        saved_model = self.db.query(Model).filter_by(id="test-model-001").first()
        assert saved_model is not None
        assert saved_model.name == "Test Model"

    def test_transaction_rollback_on_error(self):
        """测试：出错时事务正确回滚"""
        # Arrange - 创建第一个模型
        model1 = Model(id="model-1", name="Model 1", type="llm", source="local", path="/1")
        self.db.add(model1)
        self.db.commit()

        # Act & Assert - 尝试插入重复 ID
        duplicate_model = Model(id="model-1", name="Duplicate", type="llm", source="local", path="/2")
        self.db.add(duplicate_model)

        with pytest.raises(Exception):  # 期望抛出异常
            self.db.commit()

        # 事务应该回滚，第一个模型仍然存在
        count = self.db.query(Model).count()
        assert count == 1  # 只有第一个模型

    def test_model_deployment_relationship(self):
        """测试：模型和部署的外键关系"""
        # Arrange
        model = Model(id="parent-model", name="Parent", type="llm", source="local", path="/p")
        self.db.add(model)
        self.db.commit()

        deployment = Deployment(
            id="dep-1",
            model_id="parent-model",
            status="deploying",
            gpu_count=1
        )

        # Act
        self.db.add(deployment)
        self.db.commit()

        # Assert - 验证关系
        model_with_deployment = self.db.query(Model).filter_by(id="parent-model").first()
        assert len(model_with_deployment.deployments) == 1
        assert model_with_deployment.deployments[0].id == "dep-1"
```

## 端到端测试指南

### Playwright E2E 测试

```typescript
// frontend/tests/e2e/model-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('模型管理工作流', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.getByLabel('邮箱').fill('test@beaverchain.com');
    await page.getByLabel('密码').fill('testpassword');
    await page.getByRole('button', { name: '登录' }).click();

    // 等待登录完成并跳转
    await expect(page).toHaveURL('/dashboard');
  });

  test('用户可以创建、查看、更新和删除模型', async ({ page }) => {
    // 1. 导航到模型列表页
    await page.getByRole('link', { name: '模型' }).click();
    await expect(page).toHaveURL('/models');

    // 2. 创建新模型
    await page.getByRole('button', { name: '新建模型' }).click();
    await page.getByLabel('模型名称').fill('e2e-test-model');
    await page.getByLabel('模型类型').selectOption('LLM');
    await page.getByLabel('来源').selectOption('Hugging Face');
    await page.getByLabel('路径').fill('org/e2e-test-model');
    await page.getByRole('button', { name: '创建' }).click();

    // 验证创建成功
    await expect(page.getByText('模型创建成功')).toBeVisible();
    await expect(page.getByText('e2e-test-model')).toBeVisible();

    // 3. 查看模型详情
    await page.getByText('e2e-test-model').click();
    await expect(page).toHaveURL(/\/models\/.+/);
    await expect(page.getByText('e2e-test-model')).toBeVisible();

    // 4. 更新模型状态
    await page.getByRole('button', { name: '激活' }).click();
    await expect(page.getByText('状态已更新为 active')).toBeVisible();

    // 5. 删除模型
    await page.getByRole('button', { name: '删除' }).click();
    await page.getByRole('dialog').getByRole('button', { name: '确认' }).click();

    // 验证删除成功
    await expect(page.getByText('模型已删除')).toBeVisible();
    await expect(page.getByText('e2e-test-model')).not.toBeVisible();
  });

  test('模型搜索和筛选功能', async ({ page }) => {
    // 创建多个测试模型
    // ...

    // 测试搜索
    await page.getByPlaceholder('搜索模型...').fill('test');
    await page.keyboard.press('Enter');

    // 验证搜索结果
    const cards = page.getByTestId('model-card');
    await expect(cards).toHaveCount(3);

    // 测试按类型筛选
    await page.getByLabel('类型').selectOption('LLM');
    // ...
  });
});
```

## 性能测试指南

### Locust 负载测试

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between, tag
import json


class ModelServingUser(HttpUser):
    """模型服务用户行为模拟"""

    wait_time = between(1, 5)  # 请求间隔 1-5 秒

    def on_start(self):
        """每个用户启动时执行"""
        # 获取认证 token
        response = self.client.post(
            "/api/v1/auth/token",
            json={"username": "test", "password": "test123"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)  # 权重：3 倍
    def list_models(self):
        """列出模型 - 高频操作"""
        self.client.get(
            "/api/v1/models?page_size=20",
            headers=self.headers
        )

    @task(2)
    def get_model_detail(self):
        """获取模型详情"""
        # 先获取一个模型 ID
        response = self.client.get(
            "/api/v1/models?page_size=1",
            headers=self.headers
        )
        models = response.json()["items"]
        if models:
            model_id = models[0]["id"]
            self.client.get(
                f"/api/v1/models/{model_id}",
                headers=self.headers
            )

    @task(1)
    def model_inference(self):
        """模型推理 - 核心性能测试"""
        self.client.post(
            "/api/v1/inference/generate",
            headers=self.headers,
            json={
                "model_id": "test-model",
                "prompt": "Explain the concept of machine learning",
                "max_tokens": 256,
                "temperature": 0.7
            }
        )

    @tag("batch")
    @task
    def batch_inference(self):
        """批量推理测试"""
        self.client.post(
            "/api/v1/inference/batch",
            headers=self.headers,
            json={
                "model_id": "test-model",
                "prompts": [
                    "Prompt 1",
                    "Prompt 2",
                    "Prompt 3",
                    "Prompt 4",
                    "Prompt 5"
                ],
                "max_tokens": 128
            }
        )
```

### 运行性能测试

```bash
# 启动 Locust Web UI
locust -f tests/performance/locustfile.py

# 无头模式运行
locust -f tests/performance/locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --host http://localhost:8000 \
  --html reports/performance.html
```

### 基准测试

```python
# tests/performance/benchmark.py
import time
import statistics
from functools import wraps
from dataclasses import dataclass
from typing import List, Callable, Any


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    mean_time: float
    median_time: float
    min_time: float
    max_time: float
    std_dev: float
    p95_time: float
    p99_time: float


def benchmark(iterations: int = 100, warmup: int = 10):
    """
    基准测试装饰器

    Args:
        iterations: 执行次数
        warmup: 预热次数
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs) -> BenchmarkResult:
            # 预热
            for _ in range(warmup):
                func(*args, **kwargs)

            # 正式测试
            times: List[float] = []
            for _ in range(iterations):
                start = time.perf_counter()
                func(*args, **kwargs)
                end = time.perf_counter()
                times.append((end - start) * 1000)  # 转换为毫秒

            # 计算统计数据
            times_sorted = sorted(times)
            return BenchmarkResult(
                name=func.__name__,
                iterations=iterations,
                mean_time=statistics.mean(times),
                median_time=statistics.median(times),
                min_time=min(times),
                max_time=max(times),
                std_dev=statistics.stdev(times) if iterations > 1 else 0,
                p95_time=times_sorted[int(iterations * 0.95)],
                p99_time=times_sorted[int(iterations * 0.99)]
            )

        return wrapper
    return decorator


# 使用示例
@benchmark(iterations=1000, warmup=100)
def benchmark_model_loading():
    """基准测试：模型加载"""
    model = ModelLoader.load("/path/to/model", quantization="awq")
    return model


@benchmark(iterations=100, warmup=10)
def benchmark_inference_latency():
    """基准测试：推理延迟"""
    result = model.generate(
        prompt="Hello, world!",
        max_tokens=256
    )
    return result


if __name__ == "__main__":
    # 运行所有基准测试
    results = [
        benchmark_model_loading(),
        benchmark_inference_latency(),
    ]

    # 打印报告
    print("\n" + "=" * 80)
    print("基准测试报告".center(80))
    print("=" * 80)

    for result in results:
        print(f"\n{result.name}:")
        print(f"  迭代次数: {result.iterations}")
        print(f"  平均延迟: {result.mean_time:.2f}ms")
        print(f"  中位数延迟: {result.median_time:.2f}ms")
        print(f"  最小延迟: {result.min_time:.2f}ms")
        print(f"  最大延迟: {result.max_time:.2f}ms")
        print(f"  P95 延迟: {result.p95_time:.2f}ms")
        print(f"  P99 延迟: {result.p99_time:.2f}ms")
        print(f"  标准差: {result.std_dev:.2f}ms")
```

## 测试数据管理

### 测试数据工厂

```python
# tests/factories.py
import factory
from datetime import datetime, timedelta

from core.models import Model, Deployment, User
from core.database import SessionLocal


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """用户测试数据工厂"""

    class Meta:
        model = User
        sqlalchemy_session = SessionLocal()
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: f"user-{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)


class ModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    """模型测试数据工厂"""

    class Meta:
        model = Model
        sqlalchemy_session = SessionLocal()
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: f"model-{n}")
    name = factory.Sequence(lambda n: f"Test Model {n}")
    type = "llm"
    source = "huggingface"
    path = factory.Sequence(lambda n: f"org/model-{n}")
    status = "inactive"
    created_at = factory.LazyFunction(datetime.utcnow)
    created_by = factory.SubFactory(UserFactory)


class DeploymentFactory(factory.alchemy.SQLAlchemyModelFactory):
    """部署测试数据工厂"""

    class Meta:
        model = Deployment
        sqlalchemy_session = SessionLocal()
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: f"deployment-{n}")
    model = factory.SubFactory(ModelFactory)
    model_id = factory.SelfAttribute("model.id")
    status = "deploying"
    gpu_count = 1
    created_at = factory.LazyFunction(datetime.utcnow)
```

### 使用测试数据工厂

```python
def test_deployment_listing(client, db_session):
    """使用工厂创建测试数据"""
    # 创建用户
    user = UserFactory()

    # 创建 5 个模型
    models = ModelFactory.create_batch(5, created_by=user)

    # 为每个模型创建 2 个部署
    for model in models:
        DeploymentFactory.create_batch(2, model=model)

    # 获取部署列表
    response = client.get("/api/v1/deployments")

    # 验证
    assert response.status_code == 200
    assert len(response.json()["items"]) == 10  # 5 models * 2
```

## CI/CD 集成

### GitHub Actions 工作流

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests:
    name: 单元测试
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: 设置 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: 缓存依赖
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: 安装依赖
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt

      - name: 运行单元测试
        run: |
          pytest tests/unit/ -v \
            --cov=core \
            --cov-report=term-missing \
            --cov-report=xml:coverage.xml

      - name: 上传覆盖率报告
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml

  integration-tests:
    name: 集成测试
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: beaverchain_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: 设置 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: 安装依赖
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt

      - name: 运行集成测试
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/beaverchain_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/integration/ -v

  frontend-tests:
    name: 前端测试
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: 设置 Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: 安装依赖
        working-directory: frontend
        run: npm ci

      - name: 运行前端测试
        working-directory: frontend
        run: npm run test:coverage

      - name: 类型检查
        working-directory: frontend
        run: npx tsc --noEmit

  e2e-tests:
    name: E2E 测试
    runs-on: ubuntu-latest
    needs: [integration-tests, frontend-tests]
