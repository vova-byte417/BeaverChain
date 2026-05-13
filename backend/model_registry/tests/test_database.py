"""
Model Registry - 数据库服务单元测试
"""
import pytest
import tempfile
import os
import sys

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import (
    ModelVersionCreate,
    ModelVersionUpdate,
    VersionStatus,
    RollbackRequest,
    WeightsConfig,
    PromptConfig,
    RAGConfig,
    GuardrailsConfig,
    InferenceParams,
    EvaluationMetrics,
)
from services.database import DatabaseService


@pytest.fixture
def test_db():
    """创建测试数据库"""
    # 使用临时 SQLite 数据库
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db_url = f"sqlite:///{db_path}"
    db = DatabaseService(db_url)
    
    yield db
    
    # 清理
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def sample_model_data():
    """示例模型版本数据"""
    return ModelVersionCreate(
        name="test-model",
        version="1.0.0",
        description="测试模型版本",
        status=VersionStatus.DRAFT,
        tags=["test", "gpt-4"],
        weights_config=WeightsConfig(
            model_type="gpt4",
            provider="openai",
            model_id="gpt-4-turbo-preview",
            parameters={"temperature": 0.7}
        ),
        prompt_config=PromptConfig(
            system_prompt="你是一个有用的助手",
            variables=["user_query"]
        ),
        rag_config=RAGConfig(
            enabled=True,
            knowledge_base_id="kb_001",
            top_k=5
        ),
        guardrails_config=GuardrailsConfig(
            toxicity_filter_enabled=True,
            toxicity_threshold=0.7
        ),
        inference_params=InferenceParams(
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9
        ),
        evaluation_metrics=EvaluationMetrics(
            hallucination_rate=0.05,
            toxicity_score=0.01,
            faithfulness=0.95,
            avg_latency_ms=420
        )
    )


class TestDatabaseService:
    """数据库服务测试"""
    
    def test_create_model_version(self, test_db, sample_model_data):
        """测试创建模型版本"""
        result = test_db.create_model_version(sample_model_data)
        
        assert result is not None
        assert result.id is not None
        assert result.name == "test-model"
        assert result.version == "1.0.0"
        assert result.status == VersionStatus.DRAFT
        assert result.weights_config is not None
        assert result.weights_config.model_type == "gpt4"
    
    def test_create_duplicate_version(self, test_db, sample_model_data):
        """测试创建重复版本"""
        test_db.create_model_version(sample_model_data)
        
        # 再次创建相同版本应该失败
        with pytest.raises(ValueError, match="already exists"):
            test_db.create_model_version(sample_model_data)
    
    def test_get_model_version(self, test_db, sample_model_data):
        """测试获取模型版本"""
        created = test_db.create_model_version(sample_model_data)
        
        retrieved = test_db.get_model_version(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
        assert retrieved.version == created.version
    
    def test_get_model_version_not_found(self, test_db):
        """测试获取不存在的模型版本"""
        result = test_db.get_model_version("nonexistent_id")
        assert result is None
    
    def test_get_by_name_and_version(self, test_db, sample_model_data):
        """测试通过名称和版本号获取"""
        created = test_db.create_model_version(sample_model_data)
        
        retrieved = test_db.get_model_version_by_name_and_version(
            name="test-model",
            version="1.0.0"
        )
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    def test_list_model_versions(self, test_db, sample_model_data):
        """测试列出模型版本"""
        # 创建多个版本
        for i in range(3):
            data = sample_model_data.copy(update={"version": f"1.0.{i}"})
            test_db.create_model_version(data)
        
        versions, total = test_db.list_model_versions()
        
        assert total == 3
        assert len(versions) == 3
    
    def test_list_with_filters(self, test_db, sample_model_data):
        """测试带过滤的列表查询"""
        # 创建不同状态的版本
        for status in [VersionStatus.DRAFT, VersionStatus.TESTING, VersionStatus.PRODUCTION]:
            data = sample_model_data.copy(update={
                "version": f"1.0.{list(VersionStatus).index(status)}",
                "status": status
            })
            test_db.create_model_version(data)
        
        # 按状态过滤
        versions, total = test_db.list_model_versions(status=VersionStatus.PRODUCTION)
        assert total == 1
        assert versions[0].status == VersionStatus.PRODUCTION
    
    def test_list_with_pagination(self, test_db, sample_model_data):
        """测试分页功能"""
        # 创建 5 个版本
        for i in range(5):
            data = sample_model_data.copy(update={"version": f"1.0.{i}"})
            test_db.create_model_version(data)
        
        # 第一页，每页 2 条
        page1, total = test_db.list_model_versions(skip=0, limit=2)
        assert len(page1) == 2
        assert total == 5
        
        # 第二页
        page2, _ = test_db.list_model_versions(skip=2, limit=2)
        assert len(page2) == 2
        
        # 第三页
        page3, _ = test_db.list_model_versions(skip=4, limit=2)
        assert len(page3) == 1
    
    def test_update_model_version(self, test_db, sample_model_data):
        """测试更新模型版本"""
        created = test_db.create_model_version(sample_model_data)
        
        # 更新描述和状态
        update_data = ModelVersionUpdate(
            description="更新后的描述",
            status=VersionStatus.PRODUCTION
        )
        
        updated = test_db.update_model_version(created.id, update_data)
        
        assert updated is not None
        assert updated.description == "更新后的描述"
        assert updated.status == VersionStatus.PRODUCTION
        assert updated.updated_at > created.updated_at
    
    def test_update_not_found(self, test_db):
        """测试更新不存在的版本"""
        update_data = ModelVersionUpdate(description="test")
        result = test_db.update_model_version("nonexistent", update_data)
        assert result is None
    
    def test_delete_model_version(self, test_db, sample_model_data):
        """测试删除模型版本（软删除）"""
        created = test_db.create_model_version(sample_model_data)
        
        result = test_db.delete_model_version(created.id)
        assert result is True
        
        # 验证状态变为 archived
        deleted = test_db.get_model_version(created.id)
        assert deleted.status == VersionStatus.ARCHIVED
    
    def test_delete_not_found(self, test_db):
        """测试删除不存在的版本"""
        result = test_db.delete_model_version("nonexistent")
        assert result is False
    
    def test_hard_delete_model_version(self, test_db, sample_model_data):
        """测试硬删除"""
        created = test_db.create_model_version(sample_model_data)
        
        result = test_db.hard_delete_model_version(created.id)
        assert result is True
        
        # 验证彻底删除
        retrieved = test_db.get_model_version(created.id)
        assert retrieved is None
    
    def test_compare_versions(self, test_db, sample_model_data):
        """测试版本对比"""
        # 创建 v1
        v1 = test_db.create_model_version(sample_model_data)
        
        # 创建 v2（修改一些配置）
        v2_data = sample_model_data.copy(update={
            "version": "2.0.0",
            "inference_params": InferenceParams(
                temperature=0.9,  # 修改
                max_tokens=4096,  # 修改
                top_p=0.95        # 修改
            ),
            "evaluation_metrics": EvaluationMetrics(
                hallucination_rate=0.03,
                toxicity_score=0.02,
                faithfulness=0.97,
                avg_latency_ms=380
            )
        })
        v2 = test_db.create_model_version(v2_data)
        
        # 对比版本
        diff = test_db.compare_versions(v1.id, v2.id)
        
        assert diff is not None
        assert diff.base_version_id == v1.id
        assert diff.target_version_id == v2.id
        assert len(diff.changed_fields) > 0
        
        # 验证评估指标变化被检测到
        assert diff.evaluation_changes is not None
        assert "hallucination_rate" in diff.evaluation_changes
    
    def test_compare_versions_not_found(self, test_db):
        """测试对比不存在的版本"""
        diff = test_db.compare_versions("nonexistent1", "nonexistent2")
        assert diff is None
    
    def test_rollback_to_version_create_new(self, test_db, sample_model_data):
        """测试回滚（创建新版本）"""
        # 创建 v1
        v1 = test_db.create_model_version(sample_model_data)
        
        # 创建 v2
        v2_data = sample_model_data.copy(update={
            "version": "2.0.0",
            "inference_params": InferenceParams(temperature=0.9)
        })
        v2 = test_db.create_model_version(v2_data)
        
        # 从 v2 回滚到 v1（创建新版本）
        rollback_request = RollbackRequest(
            target_version_id=v1.id,
            reason="新版本效果不好",
            create_new_version=True
        )
        
        result = test_db.rollback_to_version(v2.id, rollback_request)
        
        assert result is not None
        assert result.version != v1.version  # 版本号应该递增
        assert result.inference_params.temperature == 0.7  # 应该恢复 v1 的配置
    
    def test_rollback_to_version_inplace(self, test_db, sample_model_data):
        """测试回滚（原地更新）"""
        # 创建 v1
        v1 = test_db.create_model_version(sample_model_data)
        
        # 创建 v2
        v2_data = sample_model_data.copy(update={
            "version": "2.0.0",
            "inference_params": InferenceParams(temperature=0.9)
        })
        v2 = test_db.create_model_version(v2_data)
        
        # 从 v2 回滚到 v1（原地更新）
        rollback_request = RollbackRequest(
            target_version_id=v1.id,
            create_new_version=False
        )
        
        result = test_db.rollback_to_version(v2.id, rollback_request)
        
        assert result is not None
        assert result.id == v2.id  # 应该是同一个 ID
        assert result.inference_params.temperature == 0.7  # 应该恢复 v1 的配置
    
    def test_rollback_target_not_found(self, test_db, sample_model_data):
        """测试回滚目标不存在"""
        v1 = test_db.create_model_version(sample_model_data)
        
        rollback_request = RollbackRequest(
            target_version_id="nonexistent",
            create_new_version=True
        )
        
        with pytest.raises(ValueError, match="Target version not found"):
            test_db.rollback_to_version(v1.id, rollback_request)
    
    def test_get_version_history(self, test_db, sample_model_data):
        """测试获取版本历史"""
        # 创建多个版本
        versions = []
        for i in range(5):
            data = sample_model_data.copy(update={"version": f"1.0.{i}"})
            versions.append(test_db.create_model_version(data))
        
        # 获取历史
        history = test_db.get_version_history("test-model", limit=3)
        
        assert len(history) == 3
        # 按创建时间倒序，最新的在前
        assert history[0].version == "1.0.4"
        assert history[1].version == "1.0.3"
        assert history[2].version == "1.0.2"
    
    def test_get_statistics(self, test_db, sample_model_data):
        """测试获取统计信息"""
        # 创建几个不同状态的版本
        for i, status in enumerate([
            VersionStatus.DRAFT,
            VersionStatus.TESTING,
            VersionStatus.PRODUCTION,
            VersionStatus.PRODUCTION
        ]):
            data = sample_model_data.copy(update={"version": f"1.0.{i}", "status": status})
            test_db.create_model_version(data)
        
        stats = test_db.get_statistics()
        
        assert stats["total_versions"] == 4
        assert stats["unique_models"] == 1
        assert stats["status_distribution"]["production"] == 2
        assert stats["status_distribution"]["testing"] == 1
        assert stats["status_distribution"]["draft"] == 1
    
    def test_increment_version(self, test_db):
        """测试版本号递增"""
        # 正常的 semver
        assert "1.0.1" in test_db._increment_version("1.0.0")
        
        # 带后缀的版本
        assert "1.0.0-beta" in test_db._increment_version("1.0.0-beta")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
