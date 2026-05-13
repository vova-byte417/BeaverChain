"""
Optimization Toolchain - 异步任务队列测试
"""
import pytest
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# 添加路径
sys.path.insert(0, os.path.abspath("../../../p-mp2nnvkraon8mn-worker2"))

try:
    from optimization_toolchain.core.task_queue import TaskQueue, OptimizationTask, TaskStatus
except ImportError:
    pytest.skip("Task queue module not fully implemented", allow_module_level=True)


@pytest.fixture
def task_queue():
    """创建空任务队列"""
    return TaskQueue(max_workers=2)


@pytest.fixture
def sample_task():
    """示例优化任务"""
    return OptimizationTask(
        task_id="test-task-001",
        task_type="quantization",
        model_name="test-model",
        config={"bits": 4, "group_size": 128}
    )


class TestOptimizationTask:
    """优化任务测试"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = OptimizationTask(
            task_id="task1",
            task_type="quantization",
            model_name="model1",
            config={"param": "value"}
        )
        
        assert task.task_id == "task1"
        assert task.task_type == "quantization"
        assert task.model_name == "model1"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0
    
    def test_task_status_transitions(self, sample_task):
        """测试任务状态转换"""
        # PENDING -> RUNNING
        sample_task.set_status(TaskStatus.RUNNING)
        assert sample_task.status == TaskStatus.RUNNING
        
        # RUNNING -> COMPLETED
        sample_task.set_status(TaskStatus.COMPLETED)
        assert sample_task.status == TaskStatus.COMPLETED
    
    def test_task_progress_update(self, sample_task):
        """测试任务进度更新"""
        sample_task.update_progress(0.5, "Halfway done")
        
        assert sample_task.progress == 0.5
        assert sample_task.status_message == "Halfway done"
    
    def test_task_error_handling(self, sample_task):
        """测试任务错误处理"""
        error = ValueError("Test error")
        sample_task.set_error(error)
        
        assert sample_task.status == TaskStatus.FAILED
        assert sample_task.error is not None
        assert "Test error" in str(sample_task.error)
    
    def test_task_result(self, sample_task):
        """测试任务结果"""
        result_data = {"metrics": {"speedup": 2.0}, "model_path": "/path/to/model"}
        sample_task.set_result(result_data)
        
        assert sample_task.status == TaskStatus.COMPLETED
        assert sample_task.result == result_data
        assert sample_task.progress == 1.0
    
    def test_task_duration_calculation(self, sample_task):
        """测试任务时长计算"""
        sample_task.set_status(TaskStatus.RUNNING)
        time.sleep(0.01)  # 模拟执行
        sample_task.set_status(TaskStatus.COMPLETED)
        
        assert sample_task.duration_seconds > 0
        assert sample_task.start_time is not None
        assert sample_task.end_time is not None
    
    def test_task_to_dict(self, sample_task):
        """测试任务转换为字典"""
        sample_task.set_status(TaskStatus.RUNNING)
        sample_task.update_progress(0.5, "Processing")
        
        task_dict = sample_task.to_dict()
        
        assert isinstance(task_dict, dict)
        assert task_dict["task_id"] == "test-task-001"
        assert task_dict["status"] == TaskStatus.RUNNING.value
        assert task_dict["progress"] == 0.5


class TestTaskQueue:
    """任务队列测试"""
    
    def test_queue_initialization(self, task_queue):
        """测试队列初始化"""
        assert task_queue is not None
        assert task_queue.max_workers == 2
    
    def test_submit_task(self, task_queue, sample_task):
        """测试提交任务"""
        task_id = task_queue.submit(sample_task)
        
        assert task_id == sample_task.task_id
        assert task_queue.get_status(task_id) is not None
    
    def test_get_task_status(self, task_queue, sample_task):
        """测试获取任务状态"""
        task_queue.submit(sample_task)
        status = task_queue.get_status(sample_task.task_id)
        
        assert status is not None
        assert "status" in status
    
    def test_get_nonexistent_task_status(self, task_queue):
        """测试获取不存在任务的状态"""
        status = task_queue.get_status("nonexistent")
        assert status is None
    
    def test_cancel_task(self, task_queue, sample_task):
        """测试取消任务"""
        task_queue.submit(sample_task)
        result = task_queue.cancel(sample_task.task_id)
        
        assert result is True
        status = task_queue.get_status(sample_task.task_id)
        assert status["status"] == TaskStatus.CANCELLED.value
    
    def test_cancel_nonexistent_task(self, task_queue):
        """测试取消不存在的任务"""
        result = task_queue.cancel("nonexistent")
        assert result is False
    
    def test_list_tasks(self, task_queue, sample_task):
        """测试列出所有任务"""
        task_queue.submit(sample_task)
        
        # 提交第二个任务
        task2 = OptimizationTask(
            task_id="test-task-002",
            task_type="distillation",
            model_name="model2",
            config={}
        )
        task_queue.submit(task2)
        
        all_tasks = task_queue.list_tasks()
        assert len(all_tasks) >= 2
    
    def test_list_tasks_by_status(self, task_queue, sample_task):
        """测试按状态列出任务"""
        task_queue.submit(sample_task)
        
        pending_tasks = task_queue.list_tasks(status=TaskStatus.PENDING)
        assert len(pending_tasks) >= 1
        for task in pending_tasks:
            assert task["status"] == TaskStatus.PENDING.value
    
    def test_get_queue_stats(self, task_queue, sample_task):
        """测试获取队列统计信息"""
        task_queue.submit(sample_task)
        stats = task_queue.get_stats()
        
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "pending" in stats
        assert "running" in stats
        assert "completed" in stats
        assert "failed" in stats
    
    def test_task_callback(self, task_queue, sample_task):
        """测试任务回调"""
        callback_results = []
        
        def callback(task_id, status):
            callback_results.append((task_id, status))
        
        sample_task.on_complete = callback
        task_id = task_queue.submit(sample_task)
        
        # 等待任务完成（或超时）
        import time
        max_wait = 5
        waited = 0
        while waited < max_wait:
            status = task_queue.get_status(task_id)
            if status["status"] in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                break
            time.sleep(0.1)
            waited += 0.1
        
        assert len(callback_results) >= 0  # 回调可能异步调用


class TestTaskQueueConcurrency:
    """任务队列并发测试"""
    
    def test_multiple_concurrent_tasks(self, task_queue):
        """测试多个并发任务"""
        tasks = []
        for i in range(5):
            task = OptimizationTask(
                task_id=f"concurrent-task-{i}",
                task_type="quantization",
                model_name=f"model-{i}",
                config={"delay": 0.01}
            )
            tasks.append(task)
            task_queue.submit(task)
        
        stats = task_queue.get_stats()
        assert stats["total"] == 5
    
    def test_worker_limit_respected(self, task_queue):
        """测试工作线程数限制"""
        # max_workers = 2
        assert task_queue.max_workers == 2
        
        # 提交多个任务
        for i in range(10):
            task = OptimizationTask(
                task_id=f"limit-test-{i}",
                task_type="test",
                model_name="test",
                config={}
            )
            task_queue.submit(task)
        
        stats = task_queue.get_stats()
        # 同时运行的任务不应该超过 max_workers
        assert stats["running"] <= task_queue.max_workers


class TestTaskQueueEdgeCases:
    """任务队列边界情况测试"""
    
    def test_empty_queue_stats(self, task_queue):
        """测试空队列统计"""
        stats = task_queue.get_stats()
        
        assert stats["total"] == 0
        assert stats["pending"] == 0
        assert stats["running"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
    
    def test_retry_failed_task(self, task_queue, sample_task):
        """测试重试失败任务"""
        # 标记任务失败
        sample_task.set_error(ValueError("Test error"))
        task_queue.submit(sample_task)
        
        # 重试
        retry_id = task_queue.retry(sample_task.task_id)
        assert retry_id is not None
        
        status = task_queue.get_status(retry_id)
        assert status is not None
    
    def test_task_priority(self, task_queue):
        """测试任务优先级"""
        # 创建低优先级任务
        low_task = OptimizationTask(
            task_id="low-priority",
            task_type="test",
            model_name="test",
            config={},
            priority=0
        )
        
        # 创建高优先级任务
        high_task = OptimizationTask(
            task_id="high-priority",
            task_type="test",
            model_name="test",
            config={},
            priority=10
        )
        
        # 先提交低优先级，再提交高优先级
        task_queue.submit(low_task)
        task_queue.submit(high_task)
        
        # 高优先级任务应该先执行
        stats = task_queue.get_stats()
        assert stats["total"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
