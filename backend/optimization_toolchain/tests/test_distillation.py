"""
测试 - 知识蒸馏引擎
"""
import pytest
import tempfile
import os

from ..engines.distillation import (
    KnowledgeDistiller,
    DistillationConfig,
    DistillationMode,
    TeacherModel,
    StudentModel,
    TeacherConfig,
    StudentConfig,
)


class TestTeacherModel:
    """测试教师模型"""
    
    def test_init(self):
        """测试初始化"""
        config = TeacherConfig(
            model_name_or_path="teacher-model",
            tokenizer_name="teacher-tokenizer",
        )
        teacher = TeacherModel(config)
        assert teacher is not None
        assert teacher.config.model_name_or_path == "teacher-model"
    
    def test_load(self):
        """测试加载"""
        config = TeacherConfig(model_name_or_path="teacher-test")
        teacher = TeacherModel(config)
        result = teacher.load()
        assert result is not None
    
    def test_generate(self):
        """测试生成"""
        config = TeacherConfig(model_name_or_path="teacher-gen")
        teacher = TeacherModel(config)
        teacher.load()
        result = teacher.generate(["Hello, world!"])
        assert len(result) == 1
        assert "Teacher response" in result[0]


class TestStudentModel:
    """测试学生模型"""
    
    def test_init(self):
        """测试初始化"""
        config = StudentConfig(
            model_name_or_path="student-model",
            tokenizer_name="student-tokenizer",
            num_layers=6,
            hidden_size=512,
        )
        student = StudentModel(config)
        assert student is not None
        assert student.config.num_layers == 6
        assert student.config.hidden_size == 512
    
    def test_save(self):
        """测试保存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StudentConfig(model_name_or_path="student-save")
            student = StudentModel(config)
            student.save(tmpdir)
            config_path = os.path.join(tmpdir, "student_config.json")
            assert os.path.exists(config_path)


class TestDistillationConfig:
    """测试蒸馏配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = DistillationConfig(
            name="test-distill",
            teacher_model="teacher",
            student_model="student",
        )
        assert config.mode == DistillationMode.STANDARD
        assert config.temperature == 1.0
        assert config.alpha == 0.5
        assert config.num_epochs == 3
        assert config.batch_size == 8
        assert config.learning_rate == 1e-4
    
    def test_validate_config_valid(self):
        """测试有效配置验证"""
        config = DistillationConfig(
            name="test-valid",
            teacher_model="teacher",
            student_model="student",
            temperature=2.0,
            alpha=0.7,
            num_epochs=10,
        )
        assert config.validate() is True
    
    def test_validate_config_invalid_temperature(self):
        """测试无效温度"""
        config = DistillationConfig(
            name="test-invalid-temp",
            teacher_model="teacher",
            student_model="student",
            temperature=0,  # 必须 >= 1
        )
        assert config.validate() is False
    
    def test_validate_config_invalid_alpha(self):
        """测试无效 alpha"""
        config = DistillationConfig(
            name="test-invalid-alpha",
            teacher_model="teacher",
            student_model="student",
            alpha=-0.1,  # 必须 [0, 1]
        )
        assert config.validate() is False


class TestKnowledgeDistiller:
    """测试知识蒸馏器"""
    
    def test_init(self):
        """测试初始化"""
        config = DistillationConfig(
            name="test-init",
            teacher_model="teacher",
            student_model="student",
        )
        distiller = KnowledgeDistiller(config)
        assert distiller is not None
        assert distiller.config.name == "test-init"
    
    def test_distill_basic(self):
        """测试基本蒸馏流程"""
        config = DistillationConfig(
            name="test-basic-distill",
            teacher_model="teacher",
            student_model="student",
            num_epochs=1,
            batch_size=2,
        )
        distiller = KnowledgeDistiller(config)
        result = distiller.distill()
        assert result["success"] is True
        assert result["best_val_loss"] > 0
    
    def test_distill_progress(self):
        """测试蒸馏进度"""
        config = DistillationConfig(
            name="test-progress",
            teacher_model="teacher",
            student_model="student",
            num_epochs=2,
        )
        distiller = KnowledgeDistiller(config)
        result = distiller.distill()
        assert "progress" in result
        assert result["progress"]["epochs"] == 2
        assert result["progress"]["batches_processed"] > 0


class TestDistillationResult:
    """测试蒸馏结果"""
    
    def test_student_performance(self):
        """测试学生模型性能指标"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DistillationConfig(
                name="test-performance",
                teacher_model="teacher",
                student_model="student",
                output_dir=tmpdir,
            )
            distiller = KnowledgeDistiller(config)
            result = distiller.distill()
            
            # 验证结果包含性能指标
            assert "student_model_path" in result
            assert "best_val_loss" in result
            assert "progress" in result
            assert "distillation_ratio" in result
            assert "compression_ratio" in result


class TestDistillationWorkflow:
    """测试完整蒸馏工作流"""
    
    def test_full_workflow(self):
        """测试完整蒸馏流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DistillationConfig(
                name="test-full-workflow",
                teacher_model="teacher-model",
                student_model="student-model",
                mode=DistillationMode.STANDARD,
                temperature=2.0,
                alpha=0.6,
                num_epochs=2,
                batch_size=4,
                learning_rate=5e-5,
                output_dir=tmpdir,
            )
            
            result = KnowledgeDistiller.run_distillation(config)
            
            assert result["success"] is True
            assert result["teacher_model"] == "teacher-model"
            assert result["student_model"] == "student-model"
            assert result["mode"] == "standard"
            assert "student_model_path" in result
            assert "best_val_loss" in result
            assert result["best_val_loss"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
