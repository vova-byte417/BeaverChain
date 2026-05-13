# BeaverChain 单元测试指南

## 📋 目录

1. [概述](#概述)
2. [后端测试](#后端测试)
3. [前端测试](#前端测试)
4. [覆盖率要求](#覆盖率要求)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)

---

## 概述

BeaverChain 项目使用两套测试框架：

- **后端**: pytest (Python)
- **前端**: Vitest (TypeScript/React)

### 项目结构

```
tests/
├── backend/                    # 后端测试
│   ├── __init__.py
│   ├── conftest.py            # pytest 配置和 fixtures
│   ├── test_optimization_registry.py
│   ├── test_quantization.py
│   ├── test_distillation.py
│   ├── test_inference_engines.py
│   ├── test_task_queue.py
│   └── ...
└── frontend/                   # 前端测试
    ├── vitest.config.ts
    ├── setup.ts
    ├── utils/
    │   └── cn.test.ts
    ├── components/
    │   └── ui/
    │       ├── Button.test.tsx
    │       ├── Card.test.tsx
    │       └── ...
    └── pages/
        ├── Dashboard.test.tsx
        ├── Models.test.tsx
        └── ...
```

---

## 后端测试

### 快速开始

```bash
# 安装依赖
pip install pytest pytest-cov pytest-asyncio pytest-mock httpx

# 运行所有后端测试
cd tests/backend
pytest

# 运行特定测试文件
pytest test_quantization.py

# 运行特定测试用例
pytest test_quantization.py::TestGPTQQuantizer::test_gptq_initialization

# 生成覆盖率报告
pytest --cov=. --cov-report=html --cov-report=term
```

### 测试分类

使用 markers 对测试进行分类：

```bash
# 仅运行单元测试
pytest -m unit

# 仅运行集成测试
pytest -m integration

# 跳过慢速测试
pytest -m "not slow"

# 运行特定模块测试
pytest -m model_registry
```

### 编写测试指南

#### 1. Fixture 使用

```python
import pytest

@pytest.fixture
def sample_data():
    """准备测试数据"""
    return {"key": "value"}

def test_something(sample_data):
    assert sample_data["key"] == "value"
```

#### 2. Mock 外部依赖

```python
from unittest.mock import Mock, patch

def test_api_call():
    with patch('module.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"status": "ok"}
        result = my_function()
        assert result == {"status": "ok"}
```

#### 3. 异常测试

```python
import pytest

def test_error_handling():
    with pytest.raises(ValueError, match="expected error message"):
        function_that_raises()
```

#### 4. 参数化测试

```python
@pytest.mark.parametrize("bits,group_size", [
    (4, 128),
    (8, 64),
    (4, 256),
])
def test_quantization_different_configs(bits, group_size):
    quantizer = GPTQQuantizer(bits=bits, group_size=group_size)
    assert quantizer.bits == bits
```

---

## 前端测试

### 快速开始

```bash
# 安装依赖
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom

# 运行所有前端测试
cd tests/frontend
npx vitest run

# 监听模式（开发时）
npx vitest

# 运行特定测试
npx vitest run Button.test.tsx

# 生成覆盖率
npx vitest run --coverage
```

### 测试类型

#### 1. 工具函数测试

```typescript
import { describe, it, expect } from 'vitest'
import { cn } from '@/utils/cn'

describe('cn utility', () => {
  it('should merge class names', () => {
    expect(cn('a', 'b')).toBe('a b')
  })
})
```

#### 2. 组件测试

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Button from '@/components/ui/Button'

describe('Button', () => {
  it('should handle clicks', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalled()
  })
})
```

#### 3. 页面测试

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Dashboard from '@/pages/Dashboard'

describe('Dashboard Page', () => {
  it('should render title', () => {
    render(<Dashboard />)
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
  })
})
```

---

## 覆盖率要求

### 最低标准

| 指标 | 要求 |
|-----|------|
| 行覆盖率 | >= 80% |
| 函数覆盖率 | >= 80% |
| 分支覆盖率 | >= 80% |

### 查看覆盖率报告

```bash
# 后端
pytest --cov=. --cov-report=html
open htmlcov/index.html

# 前端
npx vitest run --coverage
open coverage/index.html
```

### 排除文件

在配置中排除不需要测试的文件：

- `__init__.py`
- 配置文件 (`*.config.*`)
- 第三方代码
- 自动生成的代码

---

## 最佳实践

### 1. 测试命名

- **描述性命名**: `test_should_return_error_when_input_invalid`
- **遵循 Given-When-Then 模式**

```python
def test_should_return_404_when_model_not_found():
    # Given - 准备测试环境
    client = TestClient(app)
    
    # When - 执行操作
    response = client.get('/models/nonexistent')
    
    # Then - 验证结果
    assert response.status_code == 404
```

### 2. 测试隔离

- 每个测试应该独立运行
- 不要依赖其他测试的副作用
- 使用 fixture 进行 setup/teardown

### 3. 边界测试

```python
@pytest.mark.parametrize("value", [
    0,
    -1,
    sys.maxsize,
    None,
    "",
])
def test_boundary_conditions(value):
    # 测试边界情况
    ...
```

### 4. 错误路径测试

```python
def test_network_error_handling():
    """测试网络错误时的优雅处理"""
    with patch('api.request', side_effect=ConnectionError):
        result = fetch_data()
        assert result["status"] == "error"
        assert "retry" in result["message"]
```

---

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: pytest --cov=. --cov-fail-under=80

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx vitest run --coverage --lines 80
```

---

## 常见问题

### Q: 测试运行太慢怎么办？

A: 
1. 使用 `@pytest.mark.slow` 标记慢速测试
2. CI 中可以并行运行测试 (`pytest-xdist`)
3. Mock 昂贵的外部调用

### Q: 如何处理需要数据库的测试？

A:
1. 使用临时 SQLite 数据库
2. 使用测试容器 (testcontainers)
3. Mock 数据库层

### Q: 前端测试中 window API 不可用？

A: 在 `setup.ts` 中添加 Mock：

```typescript
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))
```

### Q: 覆盖率总是达不到 80%？

A:
1. 检查是否有未测试的错误路径
2. 确认边界条件是否覆盖
3. 合理排除不需要测试的文件

---

## 相关资源

- [pytest 官方文档](https://docs.pytest.org/)
- [Vitest 官方文档](https://vitest.dev/)
- [Testing Library 文档](https://testing-library.com/)
