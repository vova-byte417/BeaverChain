# BeaverChain 单元测试模块

## 📋 概述

本模块为 BeaverChain 系统提供完整的单元测试覆盖，包含后端和前端两大部分。

## 📦 内容

### 后端测试 (pytest)

| 测试文件 | 覆盖模块 | 用例数 |
|---------|---------|--------|
| `test_optimization_registry.py` | 优化器注册表 | 15 |
| `test_quantization.py` | 量化引擎 (GPTQ, AWQ, SqueezeLLM) | 25 |
| `test_distillation.py` | 知识蒸馏 | 20 |
| `test_inference_engines.py` | 推理引擎 (vLLM, DeepSpeed, TGI) | 25 |
| `test_task_queue.py` | 异步任务队列 | 20 |
| **总计** | | **~105** |

### 前端测试 (Vitest)

| 测试文件 | 覆盖模块 | 用例数 |
|---------|---------|--------|
| `utils/cn.test.ts` | 工具函数 | 9 |
| `components/ui/Button.test.tsx` | Button 组件 | 11 |
| `components/ui/Card.test.tsx` | Card 组件 | 7 |
| `pages/Dashboard.test.tsx` | Dashboard 页面 | 6 |
| `pages/Models.test.tsx` | Models 页面 | 8 |
| **总计** | | **~41** |

### 配置文件

- `pyproject.toml` - Python 项目配置
- `pytest.ini` - pytest 配置
- `requirements-test.txt` - Python 测试依赖
- `tests/frontend/vitest.config.ts` - Vitest 配置
- `tests/frontend/setup.ts` - 测试环境初始化

## 🚀 快速开始

### 后端测试

```bash
# 安装依赖
pip install -r requirements-test.txt

# 运行所有测试
cd tests/backend
pytest

# 运行并生成覆盖率报告
pytest --cov=. --cov-report=html --cov-fail-under=80
```

### 前端测试

```bash
# 安装依赖
cd tests/frontend
npm install vitest @testing-library/react @testing-library/jest-dom jsdom

# 运行所有测试
npx vitest run

# 监听模式
npx vitest

# 生成覆盖率
npx vitest run --coverage
```

### 使用脚本运行

```bash
# 运行所有测试
chmod +x run_tests.sh
./run_tests.sh

# 仅后端测试
./run_tests.sh --backend

# 仅前端测试
./run_tests.sh --frontend

# 生成覆盖率报告
./run_tests.sh --coverage
```

## 📊 覆盖率要求

| 指标 | 最低要求 |
|-----|---------|
| 行覆盖率 | 80% |
| 函数覆盖率 | 80% |
| 分支覆盖率 | 80% |

## 📁 目录结构

```
.
├── README.md                    # 本文件
├── TESTING-GUIDE.md            # 测试指南
├── pyproject.toml              # Python 项目配置
├── pytest.ini                  # pytest 配置
├── requirements-test.txt       # Python 依赖
├── run_tests.sh               # 测试运行脚本
└── tests/
    ├── __init__.py
    ├── backend/               # 后端测试
    │   ├── __init__.py
    │   ├── conftest.py       # pytest 配置和 fixtures
    │   ├── test_optimization_registry.py
    │   ├── test_quantization.py
    │   ├── test_distillation.py
    │   ├── test_inference_engines.py
    │   └── test_task_queue.py
    └── frontend/             # 前端测试
        ├── vitest.config.ts
        ├── setup.ts
        ├── utils/
        │   └── cn.test.ts
        ├── components/
        │   └── ui/
        │       ├── Button.test.tsx
        │       └── Card.test.tsx
        └── pages/
            ├── Dashboard.test.tsx
            └── Models.test.tsx
```

## ✅ 测试特性

### 后端测试
- ✅ 完整的测试隔离 (fixtures)
- ✅ 参数化测试
- ✅ 边界条件覆盖
- ✅ 异常路径测试
- ✅ Mock 外部依赖
- ✅ 并发测试支持

### 前端测试
- ✅ 组件渲染测试
- ✅ 事件处理测试
- ✅ 状态变化测试
- ✅ Props 传递测试
- ✅ 条件渲染测试
- ✅ 浏览器 API Mock

## 📚 文档

详细使用指南请查看 [TESTING-GUIDE.md](./TESTING-GUIDE.md)

## 🧪 测试最佳实践

1. **Given-When-Then 模式** - 清晰的测试结构
2. **测试隔离** - 每个测试独立运行
3. **描述性命名** - 测试名应该说明预期行为
4. **边界覆盖** - 测试极端情况和错误路径
5. **快速反馈** - 单元测试应该在几秒内完成

## 📞 支持

如有问题，请查看：
- [pytest 文档](https://docs.pytest.org/)
- [Vitest 文档](https://vitest.dev/)
- [Testing Library 文档](https://testing-library.com/)
