# BeaverChain 测试说明文档

> 测试框架介绍、运行指南和测试策略说明

---

## 📋 目录

1. [测试框架概览](#测试框架概览)
2. [环境准备](#环境准备)
3. [运行测试](#运行测试)
4. [单元测试详解](#单元测试详解)
5. [集成测试详解](#集成测试详解)
6. [E2E 测试详解](#e2e-测试详解)
7. [性能测试](#性能测试)
8. [测试覆盖率](#测试覆盖率)
9. [CI/CD 集成](#cicd-集成)

---

## 测试框架概览

### 技术选型

| 测试类型 | 框架/工具 | 版本要求 |
|---------|----------|---------|
| **后端单元测试** | pytest | 7.4+ |
| **后端集成测试** | pytest + httpx | - |
| **前端单元测试** | Vitest | 1.0+ |
| **前端组件测试** | React Testing Library | 14.0+ |
| **E2E 测试** | Playwright | 1.40+ |
| **性能测试** | k6 / Locust | - |
| **覆盖率报告** | coverage.py + Istanbul | - |

### 测试金字塔

```
        ┌─────────────────┐
        │   E2E 测试      │  ← 端到端场景测试 (少量)
        │    (5-10%)      │
        ├─────────────────┤
        │  集成测试        │  ← 模块间交互测试 (中等)
        │    (20-30%)     │
        ├─────────────────┤
        │  单元测试        │  ← 函数/类级别测试 (大量)
        │    (60-70%)     │
        └─────────────────┘
```

### 测试目录结构

```
beaverchain/
├── backend/
│   ├── model_registry/
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py           # pytest 配置
│   │   │   ├── test_database.py       # 数据库服务测试
│   │   │   ├── test_storage.py        # 存储服务测试
│   │   │   └── test_api.py           # API 端点测试
│   │   └── ...
│   └── ...
├── frontend/
│   ├── tests/
│   │   ├── unit/                      # 单元测试
│   │   ├── integration/               # 集成测试
│   │   └── e2e/                       # E2E 测试
│   └── ...
└── tests/
    ├── e2e/                           # 全链路 E2E 测试
    ├── performance/                   # 性能测试
    └── load-test/                     # 负载测试
```

---

## 环境准备

### 后端测试环境

#### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**开发依赖包含：**
- `pytest`: 测试框架
- `pytest-asyncio`: 异步测试支持
- `pytest-cov`: 覆盖率报告
- `httpx`: HTTP 客户端测试
- `faker`: 测试数据生成
- `freezegun`: 时间冻结测试

#### 2. 配置测试数据库

使用 SQLite 作为测试数据库（默认配置，无需额外安装）：

```bash
# 设置环境变量
export ENVIRONMENT=test
export DATABASE_URL=sqlite:///./test.db

# 或者使用 .env.test 文件
cp .env.test.example .env.test
```

### 前端测试环境

```bash
cd frontend
npm install
```

### E2E 测试环境

```bash
# 安装 Playwright 浏览器
npx playwright install

# 验证安装
npx playwright --version
```

---

## 运行测试

### 后端测试

#### 运行所有测试

```bash
cd backend

# 运行所有测试
python -m pytest model_registry/tests/ -v

# 或者使用 make（如有 Makefile）
make test
```

#### 运行特定测试文件

```bash
# 只运行数据库测试
python -m pytest model_registry/tests/test_database.py -v

# 只运行 API 测试
python -m pytest model_registry/tests/test_api.py -v

# 只运行存储服务测试
python -m pytest model_registry/tests/test_storage.py -v
```

#### 运行特定测试用例

```bash
# 按名称过滤
python -m pytest model_registry/tests/ -v -k "test_create"

# 运行单个测试函数
python -m pytest model_registry/tests/test_database.py::test_create_model_version -v
```

#### 标记测试

```bash
# 只运行快速测试
python -m pytest -m "fast" -v

# 排除慢速测试
python -m pytest -m "not slow" -v

# 只运行集成测试
python -m pytest -m "integration" -v
```

### 前端测试

```bash
cd frontend

# 运行所有单元测试
npm run test

# 监听模式（文件变化自动重跑）
npm run test:watch

# 运行测试并生成覆盖率报告
npm run test:coverage

# 运行特定测试文件
npm run test -- tests/unit/components/Button.test.tsx
```

### E2E 测试

```bash
cd frontend

# 运行所有 E2E 测试
npm run test:e2e

# 以 headed 模式运行（可见浏览器）
npm run test:e2e -- --headed

# 运行特定测试文件
npm run test:e2e -- tests/e2e/model-version.spec.ts

# 生成测试报告
npm run test:e2e -- --reporter=html
```

---

## 单元测试详解

### 后端单元测试

#### 测试标记

在测试函数上使用装饰器标记：

```python
import pytest

@pytest.mark.fast
def test_something():
    pass

@pytest.mark.slow
def test_large_file_upload():
    pass

@pytest.mark.integration
def test_api_endpoint():
    pass
```

#### Fixture 使用

```python
# conftest.py 中定义
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 创建表
    from models import Base
    Base.metadata.create_all(bind=engine)
    
    yield session
    
    # 测试后清理
    session.rollback()
    session.close()

@pytest.fixture
def sample_model_version():
    """创建示例模型版本"""
    return {
        "name": "test-model",
        "version": "1.0.0",
        "status": "draft"
    }
```

#### 测试用例示例

```python
# test_database.py
def test_create_model_version(db_session, sample_model_version):
    """测试创建模型版本"""
    service = DatabaseService(db_session)
    
    # 创建版本
    version = service.create_version(sample_model_version)
    
    # 验证结果
    assert version.id is not None
    assert version.name == "test-model"
    assert version.version == "1.0.0"
    assert version.status == "draft"

def test_get_nonexistent_version(db_session):
    """测试获取不存在的版本"""
    service = DatabaseService(db_session)
    
    version = service.get_version("non-existent-id")
    assert version is None

def test_version_comparison(db_session):
    """测试版本对比"""
    service = DatabaseService(db_session)
    
    # 创建两个版本
    v1 = service.create_version({"name": "test", "version": "1.0.0"})
    v2 = service.create_version({"name": "test", "version": "1.1.0"})
    
    # 对比版本
    diff = service.compare_versions(v1.id, v2.id)
    
    assert "version" in diff.differences
    assert diff.differences["version"].old_value == "1.0.0"
    assert diff.differences["version"].new_value == "1.1.0"
```

### 前端单元测试示例

```typescript
// Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '@/components/Button'
import { describe, it, expect, vi } from 'vitest'

describe('Button Component', () => {
  it('should render correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeDefined()
  })

  it('should handle click events', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should show loading state', () => {
    render(<Button loading>Click me</Button>)
    expect(screen.getByRole('button')).toHaveAttribute('disabled')
    expect(screen.getByTestId('spinner')).toBeDefined()
  })

  it('should apply variant styles correctly', () => {
    const { container } = render(<Button variant="primary">Primary</Button>)
    expect(container.firstChild).toHaveClass('bg-primary')
  })
})
```

---

## 集成测试详解

### API 集成测试

```python
# test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_model_version_api():
    """测试创建模型版本 API"""
    response = client.post(
        "/api/v1/model-versions",
        json={
            "name": "api-test-model",
            "version": "1.0.0",
            "status": "draft",
            "description": "API 测试模型"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] == True
    assert data["data"]["name"] == "api-test-model"
    assert "id" in data["data"]

def test_list_model_versions_api():
    """测试列出模型版本 API"""
    response = client.get("/api/v1/model-versions?status=draft")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert isinstance(data["data"]["items"], list)

def test_version_comparison_api():
    """测试版本对比 API"""
    # 先创建两个版本
    v1 = client.post("/api/v1/model-versions", json={
        "name": "compare-test", "version": "1.0.0", "status": "draft"
    }).json()["data"]
    
    v2 = client.post("/api/v1/model-versions", json={
        "name": "compare-test", "version": "1.1.0", "status": "draft"
    }).json()["data"]
    
    # 调用对比 API
    response = client.get(
        f"/api/v1/model-versions/compare?base_id={v1['id']}&target_id={v2['id']}"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "differences" in data["data"]
    assert "summary" in data["data"]

@pytest.mark.asyncio
async def test_file_upload_api():
    """测试文件上传 API"""
    files = {
        "file": ("test.bin", b"test file content", "application/octet-stream")
    }
    response = client.post(
        "/api/v1/model-versions/upload/simple",
        files=files
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["size_bytes"] == len(b"test file content")
```

---

## E2E 测试详解

### Playwright 测试示例

```typescript
// model-version.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Model Version Management', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.getByLabel('邮箱').fill('admin@beaverchain.ai')
    await page.getByLabel('密码').fill('admin123')
    await page.getByRole('button', { name: '登录' }).click()
    await expect(page).toHaveURL('/dashboard')
  })

  test('should create a new model version', async ({ page }) => {
    // 导航到模型版本页面
    await page.goto('/model-versions')
    
    // 点击创建按钮
    await page.getByRole('button', { name: '创建版本' }).click()
    
    // 填写表单
    await page.getByLabel('名称').fill('e2e-test-model')
    await page.getByLabel('版本号').fill('1.0.0')
    
    // 选择状态
    await page.getByLabel('状态').selectOption('draft')
    
    // 提交表单
    await page.getByRole('button', { name: '创建' }).click()
    
    // 验证成功提示
    await expect(page.getByText('版本创建成功')).toBeVisible()
    
    // 验证列表中显示新版本
    await expect(page.getByText('e2e-test-model')).toBeVisible()
  })

  test('should compare two versions', async ({ page }) => {
    await page.goto('/model-versions')
    
    // 选择两个版本
    await page.getByRole('checkbox').nth(0).check()
    await page.getByRole('checkbox').nth(1).check()
    
    // 点击对比按钮
    await page.getByRole('button', { name: '对比版本' }).click()
    
    // 验证对比页面
    await expect(page).toHaveURL('/compare')
    await expect(page.getByText('版本对比')).toBeVisible()
    await expect(page.getByText('差异')).toBeVisible()
  })

  test('should upload a file', async ({ page }) => {
    await page.goto('/model-versions')
    
    // 进入详情页
    await page.getByText('e2e-test-model').click()
    
    // 点击上传文件
    await page.getByRole('button', { name: '上传文件' }).click()
    
    // 选择文件
    await page.setInputFiles('input[type="file"]', 'tests/fixtures/test-file.bin')
    
    // 确认上传
    await page.getByRole('button', { name: '确认上传' }).click()
    
    // 验证上传成功
    await expect(page.getByText('上传成功')).toBeVisible()
  })
})
```

### 测试 Fixture 配置

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

---

## 性能测试

### 使用 k6 进行负载测试

```javascript
// load-test.js
import http from 'k6/http'
import { check, sleep } from 'k6'

export const options = {
  stages: [
    { duration: '30s', target: 20 },    // 20 用户
    { duration: '1m', target: 50 },     // 增加到 50 用户
    { duration: '2m', target: 100 },    // 峰值 100 用户
    { duration: '1m', target: 0 },       // 逐渐降低
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],   // 95% 请求 < 500ms
    http_req_failed: ['rate<0.01'],     // 错误率 < 1%
  },
}

const BASE_URL = 'http://localhost:8000'
const HEADERS = {
  'Authorization': 'Bearer test-api-key',
  'Content-Type': 'application/json',
}

export default function () {
  // 测试列表 API
  const listResponse = http.get(
    `${BASE_URL}/api/v1/model-versions`,
    { headers: HEADERS }
  )
  
  check(listResponse, {
    'list status is 200': (r) => r.status === 200,
    'list response time < 200ms': (r) => r.timings.duration < 200,
  })
  
  // 测试创建 API
  const createResponse = http.post(
    `${BASE_URL}/api/v1/model-versions`,
    JSON.stringify({
      name: `load-test-${__VU}-${__ITER}`,
      version: '1.0.0',
      status: 'draft',
    }),
    { headers: HEADERS }
  )
  
  check(createResponse, {
    'create status is 201': (r) => r.status === 201,
    'create response time < 300ms': (r) => r.timings.duration < 300,
  })
  
  sleep(1)
}
```

**运行性能测试：**

```bash
k6 run load-test.js
```

---

## 测试覆盖率

### 后端覆盖率

```bash
cd backend

# 运行测试并生成覆盖率报告
python -m pytest model_registry/tests/ \
  --cov=model_registry \
  --cov-report=term \
  --cov-report=html \
  --cov-report=xml

# 查看报告
open htmlcov/index.html
```

### 前端覆盖率

```bash
cd frontend
npm run test:coverage

# 查看报告
open coverage/index.html
```

### 覆盖率目标

| 类型 | 最低要求 | 目标 |
|------|---------|------|
| **核心业务逻辑** | 90% | 95% |
| **API 端点** | 85% | 90% |
| **工具/辅助函数** | 80% | 85% |
| **UI 组件** | 70% | 80% |
| **整体** | 75% | 85% |

---

## CI/CD 集成

### GitHub Actions 示例

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run backend tests
        working-directory: ./backend
        run: |
          python -m pytest model_registry/tests/ \
            --cov=model_registry \
            --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Run frontend tests
        working-directory: ./frontend
        run: npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Install Playwright browsers
        working-directory: ./frontend
        run: npx playwright install --with-deps
      
      - name: Start services
        run: docker compose up -d
      
      - name: Run E2E tests
        working-directory: ./frontend
        run: npm run test:e2e
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30
```

---

## 测试最佳实践

### 1. 测试命名规范

```python
# 好的命名
def test_create_version_with_valid_data():
def test_should_raise_error_when_version_exists():
def test_rollback_should_preserve_history():

# 不好的命名
def test1():
def test_create():
def test_version():
```

### 2. 测试数据隔离

- 每个测试使用独立的测试数据
- 测试之间不要共享状态
- 使用 fixture 进行 setup 和 teardown

### 3. 断言最佳实践

```python
# 好的断言
assert version.status == "production"
assert version.created_at is not None
assert len(version.tags) == 3

# 不好的断言
assert version is not None  # 不够具体
assert True  # 无意义
```

### 4. 测试速度优化

- 使用内存数据库进行单元测试
- Mock 外部依赖（如文件存储、第三方 API）
- 并行运行测试（`pytest -n auto`）
- 标记慢速测试，CI 中选择性运行

### 5. 失败分析

- 测试失败时，记录足够的上下文信息
- E2E 测试失败自动截图和录屏
- CI 中保留测试报告和日志

---

## 📚 相关文档

- [代码结构说明](developer/code-structure.md)
- [贡献指南](developer/contributing.md)
- [E2E 测试用例列表](developer/e2e-test-cases.md)

---

*文档版本: v1.0*
*最后更新: 2026-05-12*
