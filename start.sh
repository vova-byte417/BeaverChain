#!/bin/bash
# ==============================================
# BeaverChain - 快速启动脚本（无需 Docker）
# 直接运行: bash start.sh
# ==============================================

set -e

echo "🚀 BeaverChain - 大模型构建平台"
echo "🔴 Computer-Use (CUA) Highest Priority - LOCKED & ENFORCED"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3.10+"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements-fast.txt

# 安装 Playwright 浏览器
echo "🌐 安装浏览器引擎（用于 Computer-Use）..."
playwright install chromium

# 启动服务
echo ""
echo "✅ 环境准备完成！"
echo ""
echo "🔴 Computer-Use (CUA) Highest Priority - LOCKED & ENFORCED"
echo ""
echo "启动后端服务: http://localhost:8000"
echo ""
echo "访问 API 文档: http://localhost:8000/docs"
echo "访问状态检查: http://localhost:8000/health"
echo "查看 Computer-Use 状态: http://localhost:8000/api/v1/computer-use/status"
echo ""

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
