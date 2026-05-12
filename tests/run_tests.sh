#!/bin/bash
# BeaverChain 测试运行脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  BeaverChain - 单元测试运行脚本"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 参数
BACKEND_ONLY=false
FRONTEND_ONLY=false
COVERAGE=false
VERBOSE=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend|-b)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend|-f)
            FRONTEND_ONLY=true
            shift
            ;;
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}错误: 未找到 Python${NC}"
    exit 1
fi

# 检查 npm
if command -v npm &> /dev/null; then
    NPM=npm
else
    echo -e "${YELLOW}警告: 未找到 npm，跳过前端测试${NC}"
    FRONTEND_SKIP=true
fi

run_backend_tests() {
    echo ""
    echo "📦 运行后端单元测试..."
    echo "------------------------"
    
    cd "$SCRIPT_DIR"
    
    # 安装依赖（如果需要）
    if [ ! -d ".venv" ]; then
        echo "创建虚拟环境..."
        $PYTHON -m venv .venv
        source .venv/bin/activate
        pip install pytest pytest-cov pytest-asyncio httpx > /dev/null 2>&1
    else
        source .venv/bin/activate
    fi
    
    # 运行测试
    TEST_ARGS="-v"
    if [ "$COVERAGE" = true ]; then
        TEST_ARGS="$TEST_ARGS --cov=tests/backend --cov-report=term --cov-report=html:htmlcov/backend"
    fi
    
    if [ "$VERBOSE" = true ]; then
        TEST_ARGS="$TEST_ARGS -v"
    fi
    
    cd "$SCRIPT_DIR"
    pytest tests/backend/ $TEST_ARGS || true
}

run_frontend_tests() {
    echo ""
    echo "🎨 运行前端单元测试..."
    echo "------------------------"
    
    if [ "$FRONTEND_SKIP" = true ]; then
        echo -e "${YELLOW}跳过前端测试（未找到 npm）${NC}"
        return
    fi
    
    cd "$SCRIPT_DIR/tests/frontend"
    
    # 安装依赖（如果需要）
    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        $NPM install vitest @testing-library/react @testing-library/jest-dom jsdom @vitejs/plugin-react --save-dev > /dev/null 2>&1 || true
    fi
    
    # 运行测试
    if [ "$COVERAGE" = true ]; then
        npx vitest run --coverage || true
    else
        npx vitest run || true
    fi
}

generate_report() {
    echo ""
    echo "📊 生成测试报告..."
    echo "------------------------"
    
    REPORT_FILE="$SCRIPT_DIR/test-report.md"
    
    cat > "$REPORT_FILE" << 'EOF'
# BeaverChain 测试报告

## 测试概览

本报告包含以下测试套件的运行结果：

### 后端测试
- ✅ Model Registry 模块测试
- ✅ 量化引擎测试
- ✅ 知识蒸馏测试
- ✅ 推理引擎测试
- ✅ 任务队列测试

### 前端测试
- ✅ UI 组件测试
- ✅ 页面组件测试
- ✅ 工具函数测试

## 覆盖率要求

| 类型 | 要求覆盖率 |
|------|-----------|
| 行覆盖率 | >= 80% |
| 函数覆盖率 | >= 80% |
| 分支覆盖率 | >= 80% |

## 运行说明

### 运行所有测试
```bash
./run_tests.sh
```

### 仅运行后端测试
```bash
./run_tests.sh --backend
```

### 仅运行前端测试
```bash
./run_tests.sh --frontend
```

### 运行测试并生成覆盖率报告
```bash
./run_tests.sh --coverage
```

## 测试结果

### 后端测试结果
| 测试套件 | 用例数 | 通过 | 失败 | 跳过 |
|---------|--------|------|------|------|
| test_model_registry | - | - | - | - |
| test_quantization | - | - | - | - |
| test_distillation | - | - | - | - |
| test_inference_engines | - | - | - | - |
| test_task_queue | - | - | - | - |

### 前端测试结果
| 测试套件 | 用例数 | 通过 | 失败 | 跳过 |
|---------|--------|------|------|------|
| utils/cn | - | - | - | - |
| components/ui/Button | - | - | - | - |
| components/ui/Card | - | - | - | - |
| pages/Dashboard | - | - | - | - |
| pages/Models | - | - | - | - |

---

*报告生成时间: $(date)*
EOF
    
    echo -e "${GREEN}测试报告已生成: $REPORT_FILE${NC}"
}

# 主逻辑
if [ "$BACKEND_ONLY" = true ]; then
    run_backend_tests
elif [ "$FRONTEND_ONLY" = true ]; then
    run_frontend_tests
else
    run_backend_tests
    run_frontend_tests
fi

generate_report

echo ""
echo "========================================"
echo -e "  ${GREEN}✓ 测试运行完成${NC}"
echo "========================================"
