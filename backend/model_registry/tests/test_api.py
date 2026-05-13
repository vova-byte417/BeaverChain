"""
Model Registry - API 端点测试
使用 FastAPI TestClient 进行接口测试
"""
import pytest
import tempfile
import os
import sys
from fastapi.testclient import TestClient

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models.schemas import VersionStatus


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_version_data():
    """示例模型版本数据"""
    return {
        "name": "test-model-api",
        "version": "1.0.0",
        "description": "API 测试模型",
        "status": "draft",
        "tags": ["api-test", "gpt-4"],
        "weights_config": {
            "model_type": "gpt4",
            "provider": "openai",
            "model_id": "gpt-4-turbo-preview",
            "parameters": {"temperature": 0.7}
        },
        "prompt_config": {
            "system_prompt": "你是一个有用的助手",
            "variables": ["user_query"]
        },
        "rag_config": {
            "enabled": True,
            "knowledge_base_id": "kb_001",
            "top_k": 5
        },
        "guardrails_config": {
            "toxicity_filter_enabled": True,
            "toxicity_threshold": 0.7
        },
        "inference_params": {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9
        },
        "evaluation_metrics": {
            "hallucination_rate": 0.05,
            "toxicity_score": 0.01,
            "faithfulness": 0.95,
            "avg_latency_ms": 420
        }
    }


class TestHealthEndpoints:
    """健康检查端点测试"""
    
    def test_root_redirect(self, client):
        """测试根路径重定向到文档"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [301, 302, 307]
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Model Registry"
    
    def test_db_health_check(self, client):
        """测试数据库健康检查"""
        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestModelVersionCRUD:
    """模型版本 CRUD 测试"""
    
    def test_create_model_version(self, client, sample_version_data):
        """测试创建模型版本"""
        response = client.post("/api/v1/model-versions", json=sample_version_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-model-api"
        assert data["version"] == "1.0.0"
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data
        
        # 保存 ID 供后续测试使用
        self.created_id = data["id"]
    
    def test_create_duplicate_version(self, client, sample_version_data):
        """测试创建重复版本"""
        # 第一次创建
        client.post("/api/v1/model-versions", json=sample_version_data)
        
        # 第二次创建应该失败
        response = client.post("/api/v1/model-versions", json=sample_version_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_get_model_version(self, client, sample_version_data):
        """测试获取单个模型版本"""
        # 先创建
        create_response = client.post("/api/v1/model-versions", json=sample_version_data)
        version_id = create_response.json()["id"]
        
        # 再获取
        response = client.get(f"/api/v1/model-versions/{version_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == version_id
        assert data["name"] == "test-model-api"
        assert data["weights_config"]["model_type"] == "gpt4"
    
    def test_get_model_version_not_found(self, client):
        """测试获取不存在的模型版本"""
        response = client.get("/api/v1/model-versions/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_list_model_versions(self, client, sample_version_data):
        """测试列出模型版本"""
        # 创建几个版本
        for i in range(3):
            data = sample_version_data.copy()
            data["version"] = f"1.0.{i}"
            client.post("/api/v1/model-versions", json=data)
        
        # 获取列表
        response = client.get("/api/v1/model-versions")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["total"] >= 3
    
    def test_list_with_status_filter(self, client, sample_version_data):
        """测试按状态过滤"""
        # 创建不同状态的版本
        for status in ["draft", "testing", "production"]:
            data = sample_version_data.copy()
            data["version"] = f"1.0.{status}"
            data["status"] = status
            client.post("/api/v1/model-versions", json=data)
        
        # 只获取 production 版本
        response = client.get(
            "/api/v1/model-versions",
            params={"status": "production"}
        )
        assert response.status_code == 200
        data = response.json()
        
        for version in data["data"]:
            assert version["status"] == "production"
    
    def test_list_with_pagination(self, client, sample_version_data):
        """测试分页"""
        # 创建 5 个版本
        for i in range(5):
            data = sample_version_data.copy()
            data["version"] = f"2.0.{i}"
            client.post("/api/v1/model-versions", json=data)
        
        # 第一页
        page1 = client.get("/api/v1/model-versions", params={"skip": 0, "limit": 2}).json()
        assert len(page1["data"]) == 2
        
        # 第二页
        page2 = client.get("/api/v1/model-versions", params={"skip": 2, "limit": 2}).json()
        assert len(page2["data"]) == 2
        
        # 第三页（最后一页）
        page3 = client.get("/api/v1/model-versions", params={"skip": 4, "limit": 2}).json()
        assert len(page3["data"]) >= 1
    
    def test_update_model_version(self, client, sample_version_data):
        """测试更新模型版本"""
        # 创建
        create_response = client.post("/api/v1/model-versions", json=sample_version_data)
        version_id = create_response.json()["id"]
        
        # 更新
        update_data = {
            "description": "更新后的描述",
            "status": "production",
            "tags": ["updated-tag"]
        }
        response = client.patch(
            f"/api/v1/model-versions/{version_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "更新后的描述"
        assert data["status"] == "production"
        assert "updated-tag" in data["tags"]
    
    def test_update_not_found(self, client):
        """测试更新不存在的版本"""
        update_data = {"description": "test"}
        response = client.patch(
            "/api/v1/model-versions/nonexistent-id",
            json=update_data
        )
        assert response.status_code == 404
    
    def test_delete_model_version(self, client, sample_version_data):
        """测试删除模型版本"""
        # 创建
        create_response = client.post("/api/v1/model-versions", json=sample_version_data)
        version_id = create_response.json()["id"]
        
        # 删除
        response = client.delete(f"/api/v1/model-versions/{version_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 验证状态变为 archived
        get_response = client.get(f"/api/v1/model-versions/{version_id}")
        assert get_response.json()["status"] == "archived"
    
    def test_hard_delete_model_version(self, client, sample_version_data):
        """测试硬删除"""
        # 创建
        create_response = client.post("/api/v1/model-versions", json=sample_version_data)
        version_id = create_response.json()["id"]
        
        # 硬删除
        response = client.delete(
            f"/api/v1/model-versions/{version_id}",
            params={"hard_delete": True}
        )
        assert response.status_code == 200
        
        # 验证彻底删除
        get_response = client.get(f"/api/v1/model-versions/{version_id}")
        assert get_response.status_code == 404


class TestVersionCompareAndRollback:
    """版本对比和回滚测试"""
    
    def test_compare_versions(self, client, sample_version_data):
        """测试版本对比"""
        # 创建 v1
        v1_data = sample_version_data.copy()
        v1_data["version"] = "3.0.0"
        v1 = client.post("/api/v1/model-versions", json=v1_data).json()
        
        # 创建 v2（修改一些配置）
        v2_data = sample_version_data.copy()
        v2_data["version"] = "3.1.0"
        v2_data["inference_params"]["temperature"] = 0.9
        v2_data["inference_params"]["max_tokens"] = 4096
        v2 = client.post("/api/v1/model-versions", json=v2_data).json()
        
        # 对比版本
        response = client.get(
            "/api/v1/model-versions/compare",
            params={"base_id": v1["id"], "target_id": v2["id"]}
        )
        
        assert response.status_code == 200
        diff = response.json()
        assert diff["base_version_id"] == v1["id"]
        assert diff["target_version_id"] == v2["id"]
        assert len(diff["changed_fields"]) > 0
    
    def test_compare_versions_not_found(self, client):
        """测试对比不存在的版本"""
        response = client.get(
            "/api/v1/model-versions/compare",
            params={"base_id": "nonexistent1", "target_id": "nonexistent2"}
        )
        assert response.status_code == 404
    
    def test_rollback_version(self, client, sample_version_data):
        """测试回滚版本"""
        # 创建 v1
        v1_data = sample_version_data.copy()
        v1_data["version"] = "4.0.0"
        v1 = client.post("/api/v1/model-versions", json=v1_data).json()
        
        # 创建 v2
        v2_data = sample_version_data.copy()
        v2_data["version"] = "4.1.0"
        v2_data["inference_params"]["temperature"] = 0.9
        v2 = client.post("/api/v1/model-versions", json=v2_data).json()
        
        # 从 v2 回滚到 v1
        rollback_request = {
            "target_version_id": v1["id"],
            "reason": "新版本效果不理想",
            "create_new_version": True
        }
        
        response = client.post(
            f"/api/v1/model-versions/{v2['id']}/rollback",
            json=rollback_request
        )
        
        assert response.status_code == 200
        rolled_back = response.json()
        assert rolled_back["inference_params"]["temperature"] == 0.7
    
    def test_rollback_invalid_target(self, client, sample_version_data):
        """测试回滚到不存在的目标"""
        # 创建一个版本
        v1 = client.post("/api/v1/model-versions", json=sample_version_data).json()
        
        # 尝试回滚到不存在的目标
        rollback_request = {
            "target_version_id": "nonexistent-id",
            "create_new_version": True
        }
        
        response = client.post(
            f"/api/v1/model-versions/{v1['id']}/rollback",
            json=rollback_request
        )
        assert response.status_code == 400


class TestStatisticsAndHistory:
    """统计信息和历史记录测试"""
    
    def test_get_version_history(self, client, sample_version_data):
        """测试获取版本历史"""
        model_name = "history-test-model"
        
        # 创建多个版本
        for i in range(5):
            data = sample_version_data.copy()
            data["name"] = model_name
            data["version"] = f"1.0.{i}"
            client.post("/api/v1/model-versions", json=data)
        
        # 获取历史
        response = client.get(
            f"/api/v1/model-versions/history/{model_name}",
            params={"limit": 3}
        )
        
        assert response.status_code == 200
        history = response.json()
        assert len(history) == 3
        # 按创建时间倒序
        assert history[0]["version"] > history[1]["version"]
    
    def test_get_statistics(self, client, sample_version_data):
        """测试获取统计信息"""
        response = client.get("/api/v1/model-versions/statistics/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "total_versions" in data["data"]
        assert "status_distribution" in data["data"]
        assert "recent_versions" in data["data"]


class TestFileUpload:
    """文件上传测试"""
    
    def test_simple_file_upload(self, client):
        """测试简单文件上传"""
        file_content = b"test model weights content"
        
        response = client.post(
            "/api/v1/model-versions/upload/simple",
            files={"file": ("model_weights.bin", file_content, "application/octet-stream")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "file_path" in data
        assert data["file_size"] == len(file_content)
    
    def test_initiate_chunked_upload(self, client):
        """测试初始化分片上传"""
        upload_info = {
            "file_name": "large_model.bin",
            "file_size": 1024 * 1024 * 100,  # 100MB
            "chunk_size": 5 * 1024 * 1024,  # 5MB per chunk
            "metadata": {"model_type": "gpt4"}
        }
        
        response = client.post(
            "/api/v1/model-versions/upload/init",
            json=upload_info
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "upload_id" in data
    
    def test_check_file_exists(self, client):
        """测试检查文件是否存在"""
        # 不存在的文件
        response = client.get("/api/v1/model-versions/files/nonexistent.bin/exists")
        assert response.status_code == 200
        assert response.json()["exists"] is False
    
    def test_abort_upload(self, client):
        """测试中止上传"""
        # 先初始化
        upload_info = {
            "file_name": "to_abort.bin",
            "file_size": 1024,
            "metadata": {}
        }
        init_response = client.post(
            "/api/v1/model-versions/upload/init",
            json=upload_info
        )
        upload_id = init_response.json()["upload_id"]
        
        # 中止
        response = client.post(
            f"/api/v1/model-versions/upload/abort?upload_id={upload_id}"
        )
        assert response.status_code == 200


class TestOpenAPI:
    """OpenAPI 文档测试"""
    
    def test_openapi_json(self, client):
        """测试 OpenAPI 文档生成"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert spec["info"]["title"] == "Model Registry"
    
    def test_docs_page(self, client):
        """测试 Swagger UI 文档页面"""
        response = client.get("/docs")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
