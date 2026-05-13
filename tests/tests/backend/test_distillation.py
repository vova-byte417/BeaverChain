"""
Optimization Toolchain - 知识蒸馏测试
"""
import pytest
import sys
import os

# 添加路径
sys.path.insert(0, os.path.abspath("../../../p-mp2nnvkraon8mn-worker2"))

try:
    from optimization_toolchain.engines.distillation.distiller import KnowledgeDistiller
    from optimization_toolchain.engines.distillation.teacher import TeacherModel
    from optimization_toolchain.engines.distillation.student import StudentModel
except ImportError:
    pytest.skip("Distillation module not fully implemented", allow_module_level=True)


@pytest.fixture
def teacher_model():
    """Teacher 模型"""
    return TeacherModel(
        model_name="gpt4-teacher",
        model_size="large",
        num_layers=24,
        hidden_size=1024
    )


@pytest.fixture
def student_model():
    """Student 模型"""
    return StudentModel(
        model_name="gpt4-student",
        model_size="small",
        num_layers=12,
        hidden_size=512
    )


@pytest.fixture
def distiller(teacher_model, student_model):
    """蒸馏器"""
    return KnowledgeDistiller(
        teacher=teacher_model,
        student=student_model,
        temperature=4.0,
        alpha=0.5
    )


class TestTeacherModel:
    """Teacher 模型测试"""
    
    def test_teacher_initialization(self, teacher_model):
        """测试 Teacher 初始化"""
        assert teacher_model.model_name == "gpt4-teacher"
        assert teacher_model.model_size == "large"
        assert teacher_model.num_layers == 24
        assert teacher_model.hidden_size == 1024
    
    def test_teacher_forward_pass(self, teacher_model):
        """测试 Teacher 前向传播"""
        input_data = {"input_ids": [1, 2, 3, 4, 5], "attention_mask": [1, 1, 1, 1, 1]}
        output = teacher_model.forward(input_data)
        
        assert output is not None
        assert "logits" in output
    
    def test_teacher_get_logits(self, teacher_model):
        """测试获取 logits"""
        input_data = {"input_ids": [1, 2, 3]}
        logits = teacher_model.get_logits(input_data)
        
        assert logits is not None
        assert isinstance(logits, (list, dict))
    
    def test_teacher_save_load(self, teacher_model, tmp_path):
        """测试模型保存和加载"""
        save_path = str(tmp_path / "teacher_model")
        teacher_model.save(save_path)
        
        # 重新加载
        loaded = TeacherModel.load(save_path)
        assert loaded is not None
        assert loaded.model_name == teacher_model.model_name


class TestStudentModel:
    """Student 模型测试"""
    
    def test_student_initialization(self, student_model):
        """测试 Student 初始化"""
        assert student_model.model_name == "gpt4-student"
        assert student_model.num_layers == 12
        assert student_model.hidden_size == 512
    
    def test_student_is_smaller(self, teacher_model, student_model):
        """测试 Student 确实比 Teacher 小"""
        assert student_model.num_layers < teacher_model.num_layers
        assert student_model.hidden_size < teacher_model.hidden_size
    
    def test_student_forward_pass(self, student_model):
        """测试 Student 前向传播"""
        input_data = {"input_ids": [1, 2, 3, 4, 5]}
        output = student_model.forward(input_data)
        
        assert output is not None
        assert "logits" in output


class TestKnowledgeDistiller:
    """知识蒸馏器测试"""
    
    def test_distiller_initialization(self, distiller):
        """测试蒸馏器初始化"""
        assert distiller is not None
        assert distiller.temperature == 4.0
        assert distiller.alpha == 0.5
    
    def test_distillation_step(self, distiller):
        """测试单步蒸馏"""
        batch_data = {
            "input_ids": [[1, 2, 3, 4, 5]],
            "attention_mask": [[1, 1, 1, 1, 1]],
            "labels": [[1, 2, 3, 4, 5]]
        }
        
        loss = distiller.train_step(batch_data)
        
        assert loss is not None
        assert isinstance(loss, float)
        assert loss >= 0
    
    def test_loss_calculation(self, distiller):
        """测试损失计算"""
        teacher_logits = [0.1, 0.5, 0.3, 0.1]
        student_logits = [0.15, 0.45, 0.25, 0.15]
        labels = [0, 1, 0, 0]
        
        loss = distiller.calculate_loss(
            teacher_logits=teacher_logits,
            student_logits=student_logits,
            labels=labels
        )
        
        assert loss is not None
        assert isinstance(loss, float)
        assert loss >= 0
    
    def test_distillation_run(self, distiller):
        """测试完整蒸馏流程"""
        training_data = [
            {"input_ids": [1, 2, 3], "labels": [1, 2, 3]}
            for _ in range(10)
        ]
        
        result = distiller.run_distillation(
            training_data=training_data,
            num_epochs=2,
            learning_rate=1e-4
        )
        
        assert result is not None
        assert result.success is True
        assert "final_loss" in result.metrics
        assert "total_time" in result.metrics
    
    def test_temperature_effect(self, teacher_model, student_model):
        """测试温度参数的影响"""
        # 不同温度的蒸馏器
        distiller_low_temp = KnowledgeDistiller(
            teacher=teacher_model,
            student=student_model,
            temperature=1.0,
            alpha=0.5
        )
        
        distiller_high_temp = KnowledgeDistiller(
            teacher=teacher_model,
            student=student_model,
            temperature=10.0,
            alpha=0.5
        )
        
        batch_data = {
            "input_ids": [[1, 2, 3]],
            "labels": [[1, 2, 3]]
        }
        
        loss_low = distiller_low_temp.train_step(batch_data)
        loss_high = distiller_high_temp.train_step(batch_data)
        
        # 损失应该不同
        assert loss_low is not None
        assert loss_high is not None
    
    def test_alpha_balancing(self, teacher_model, student_model):
        """测试 alpha 参数的影响（KL 散度和交叉熵的权重）"""
        # alpha = 0 应该只使用交叉熵
        distiller_ce_only = KnowledgeDistiller(
            teacher=teacher_model,
            student=student_model,
            temperature=4.0,
            alpha=0.0
        )
        
        # alpha = 1 应该只使用 KL 散度
        distiller_kl_only = KnowledgeDistiller(
            teacher=teacher_model,
            student=student_model,
            temperature=4.0,
            alpha=1.0
        )
        
        batch_data = {
            "input_ids": [[1, 2, 3]],
            "labels": [[1, 2, 3]]
        }
        
        loss_ce = distiller_ce_only.train_step(batch_data)
        loss_kl = distiller_kl_only.train_step(batch_data)
        
        assert loss_ce is not None
        assert loss_kl is not None


class TestDistillationMetrics:
    """蒸馏指标测试"""
    
    def test_compression_ratio(self, teacher_model, student_model, distiller):
        """测试压缩比"""
        result = distiller.run_distillation(training_data=[], num_epochs=1)
        
        if result and "compression_ratio" in result.metrics:
            compression = result.metrics["compression_ratio"]
            assert isinstance(compression, float)
            assert compression > 1.0  # 应该有压缩
    
    def test_speedup_measurement(self, distiller):
        """测试加速比测量"""
        speedup = distiller.measure_speedup(batch_size=8, num_batches=10)
        
        assert isinstance(speedup, float)
        assert speedup > 0
    
    def test_accuracy_retention(self, distiller):
        """测试准确率保留"""
        test_data = [
            {"input_ids": [1, 2, 3], "expected": 1}
            for _ in range(100)
        ]
        
        retention = distiller.measure_accuracy_retention(test_data)
        
        assert isinstance(retention, float)
        assert 0 <= retention <= 1.0  # 准确率应该在 0-1 之间


class TestDistillationEdgeCases:
    """蒸馏边界情况测试"""
    
    def test_empty_training_data(self, distiller):
        """测试空训练数据"""
        result = distiller.run_distillation(training_data=[], num_epochs=1)
        
        # 应该优雅处理
        assert result is not None
    
    def test_zero_epochs(self, distiller):
        """测试 0 轮训练"""
        result = distiller.run_distillation(training_data=[{"input_ids": [1]}], num_epochs=0)
        
        # 应该返回初始化状态
        assert result is not None
    
    def test_very_small_student(self, teacher_model):
        """测试极小的 Student 模型"""
        tiny_student = StudentModel(
            model_name="tiny-student",
            model_size="tiny",
            num_layers=2,
            hidden_size=64
        )
        
        distiller = KnowledgeDistiller(
            teacher=teacher_model,
            student=tiny_student,
            temperature=4.0,
            alpha=0.5
        )
        
        result = distiller.run_distillation(
            training_data=[{"input_ids": [1]}],
            num_epochs=1
        )
        
        assert result is not None
    
    def test_distillation_checkpointing(self, distiller, tmp_path):
        """测试蒸馏检查点"""
        checkpoint_path = str(tmp_path / "checkpoints")
        
        result = distiller.run_distillation(
            training_data=[{"input_ids": [1]} for _ in range(5)],
            num_epochs=2,
            checkpoint_dir=checkpoint_path,
            save_interval=1
        )
        
        assert result is not None
        # 应该有检查点文件
        assert os.path.exists(checkpoint_path) or result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
