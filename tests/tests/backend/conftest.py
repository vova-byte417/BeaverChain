"""
BeaverChain - pytest 全局配置和共享 Fixture
"""
import pytest
import tempfile
import shutil
import os
import sys

# 添加模块路径
WORKER2_PATH = os.path.abspath("../../p-mp2nnvkraon8mn-worker2")
sys.path.insert(0, WORKER2_PATH)
sys.path.insert(0, os.path.join(WORKER2_PATH, "model_registry"))
sys.path.insert(0, os.path.join(WORKER2_PATH, "optimization_toolchain"))


@pytest.fixture(scope="session")
def temp_dir():
    """会话级临时目录"""
    path = tempfile.mkdtemp(prefix="beaverchain_test_")
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def temp_file():
    """创建临时文件"""
    fd, path = tempfile.mkstemp(prefix="test_", suffix=".tmp")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def sample_model_config():
    """示例模型配置"""
    return {
        "model_name": "test-model",
        "model_type": "gpt4",
        "provider": "openai",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9
        }
    }


@pytest.fixture
def mock_response():
    """Mock API 响应"""
    return {
        "success": True,
        "data": {},
        "message": "Operation completed successfully"
    }
