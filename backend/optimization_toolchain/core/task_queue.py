"""
优化工具链 - 异步任务队列
使用 Redis Stream 或 简单的内存队列来管理优化任务
"""
import asyncio
import uuid
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque

from .base import OptimizationResult, BaseOptimizer


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"            # 等待中
    QUEUED = "queued"              # 已排队
    RUNNING = "running"            # 运行中
    COMPLETED = "completed"        # 已完成
    FAILED = "failed"              # 失败
    CANCELLED = "cancelled"        # 已取消


@dataclass
class OptimizationTask:
    """优化任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    optimizer_name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[OptimizationResult] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    progress: float = 0.0  # 0-100
    current_step: str = ""
    
    callback: Optional[Callable] = None
    error_message: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    
    priority: int = 0  # 优先级，数值越大优先级越高
    
    def add_log(self, message: str) -> None:
        """添加日志"""
        timestamp = datetime.now().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "optimizer_name": self.optimizer_name,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "log_count": len(self.logs),
            "result": self.result.to_dict() if self.result else None,
        }


class TaskQueue:
    """任务队列类"""
    
    def __init__(self, max_workers: int = 2, use_redis: bool = False):
        """
        初始化任务队列
        
        Args:
            max_workers: 最大并发工作数
            use_redis: 是否使用 Redis（如果 False 则使用内存队列）
        """
        self.max_workers = max_workers
        self.use_redis = use_redis
        
        # 内存队列
        self._pending: deque = deque()
        self._running: Dict[str, OptimizationTask] = {}
        self._completed: Dict[str, OptimizationTask] = {}
        
        # 任务回调注册
        self._callbacks: Dict[str, List[Callable]] = {}
        
        # 运行状态
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
    
    def submit(self, task: OptimizationTask) -> str:
        """
        提交任务
        
        Args:
            task: 优化任务
            
        Returns:
            任务 ID
        """
        task.status = TaskStatus.QUEUED
        task.add_log(f"任务已提交到队列，当前队列长度: {len(self._pending) + 1}")
        
        # 按优先级插入队列
        if task.priority > 0:
            # 高优先级任务插到前面
            inserted = False
            for i, t in enumerate(self._pending):
                if task.priority > t.priority:
                    self._pending.insert(i, task)
                    inserted = True
                    break
            if not inserted:
                self._pending.append(task)
        else:
            self._pending.append(task)
        
        return task.task_id
    
    def get_task(self, task_id: str) -> Optional[OptimizationTask]:
        """
        获取任务状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务对象，如果不存在则返回 None
        """
        # 先检查运行中任务
        if task_id in self._running:
            return self._running[task_id]
        
        # 再检查已完成任务
        if task_id in self._completed:
            return self._completed[task_id]
        
        # 最后检查待处理任务
        for task in self._pending:
            if task.task_id == task_id:
                return task
        
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            是否取消成功
        """
        # 从待处理队列移除
        for i, task in enumerate(self._pending):
            if task.task_id == task_id:
                task.status = TaskStatus.CANCELLED
                del self._pending[i]
                self._completed[task_id] = task
                return True
        
        # 运行中的任务无法立即取消，但可以标记
        if task_id in self._running:
            self._running[task_id].add_log("收到取消请求，将在当前步骤完成后停止")
            return True
        
        return False
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
    ) -> List[OptimizationTask]:
        """
        列出任务
        
        Args:
            status: 按状态过滤
            limit: 返回数量限制
            
        Returns:
            任务列表
        """
        all_tasks: List[OptimizationTask] = []
        
        # 待处理任务
        all_tasks.extend(self._pending)
        
        # 运行中任务
        all_tasks.extend(self._running.values())
        
        # 已完成任务（最新的在前）
        completed_list = sorted(
            self._completed.values(),
            key=lambda t: t.completed_at or t.created_at,
            reverse=True
        )
        all_tasks.extend(completed_list)
        
        # 按状态过滤
        if status:
            all_tasks = [t for t in all_tasks if t.status == status]
        
        return all_tasks[:limit]
    
    async def _worker(self):
        """工作协程"""
        while self._running:
            try:
                # 获取下一个任务
                if not self._pending:
                    await asyncio.sleep(0.1)
                    continue
                
                task = self._pending.popleft()
                
                # 开始执行
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                self._running[task.task_id] = task
                
                task.add_log("开始执行优化任务")
                
                try:
                    # 执行优化任务
                    result = await self._execute_task(task)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100.0
                    task.add_log("任务完成")
                    
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)
                    task.add_log(f"任务执行失败: {str(e)}")
                
                finally:
                    task.completed_at = datetime.now()
                    
                    # 从运行中移除，加入已完成
                    del self._running[task.task_id]
                    self._completed[task.task_id] = task
                    
                    # 触发回调
                    if task.callback:
                        try:
                            await task.callback(task)
                        except Exception as e:
                            task.add_log(f"回调执行失败: {str(e)}")
                    
                    # 触发注册的回调
                    if task.task_id in self._callbacks:
                        for callback in self._callbacks[task.task_id]:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(task)
                                else:
                                    callback(task)
                            except Exception as e:
                                task.add_log(f"回调执行失败: {str(e)}")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker error: {str(e)}")
                await asyncio.sleep(1.0)
    
    async def _execute_task(self, task: OptimizationTask) -> OptimizationResult:
        """
        执行优化任务
        
        Args:
            task: 优化任务
            
        Returns:
            优化结果
        """
        # 这里是模拟执行，实际需要调用具体的优化器
        from .registry import OptimizationRegistry
        
        # 获取优化器
        optimizer = OptimizationRegistry.create_optimizer(
            name=task.optimizer_name,
            **task.config
        )
        
        if not optimizer:
            raise ValueError(f"Unknown optimizer: {task.optimizer_name}")
        
        # 进度更新回调
        def progress_callback(step: str, progress: float):
            task.current_step = step
            task.progress = progress
            task.add_log(f"[{progress:.1f}%] {step}")
        
        # 执行优化
        result = await asyncio.to_thread(optimizer.run)
        
        return result
    
    async def start(self):
        """启动任务队列"""
        if self._running:
            return
        
        self._running = True
        
        # 启动工作协程
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker())
            self._worker_tasks.append(worker_task)
        
        print(f"Task queue started with {self.max_workers} workers")
    
    async def stop(self):
        """停止任务队列"""
        self._running = False
        
        # 取消所有工作协程
        for worker_task in self._worker_tasks:
            worker_task.cancel()
        
        # 等待所有工作协程完成
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        self._worker_tasks.clear()
    
    def register_callback(self, task_id: str, callback: Callable):
        """
        注册任务完成回调
        
        Args:
            task_id: 任务 ID
            callback: 回调函数
        """
        if task_id not in self._callbacks:
            self._callbacks[task_id] = []
        self._callbacks[task_id].append(callback)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        获取队列统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "pending": len(self._pending),
            "running": len(self._running),
            "completed": len(self._completed),
            "max_workers": self.max_workers,
            "is_running": self._running,
        }


# 全局任务队列实例
_global_queue: Optional[TaskQueue] = None


def get_global_queue(max_workers: int = 2) -> TaskQueue:
    """
    获取全局任务队列实例
    
    Args:
        max_workers: 最大并发工作数（仅在第一次调用时生效）
        
    Returns:
        全局任务队列实例
    """
    global _global_queue
    if _global_queue is None:
        _global_queue = TaskQueue(max_workers=max_workers)
    return _global_queue
