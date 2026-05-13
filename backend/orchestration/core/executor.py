"""
工作流执行器
Workflow Executor
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Set
from collections import deque

from .workflow import (
    Workflow,
    WorkflowNode,
    WorkflowContext,
    ExecutionStatus,
    NodeType,
)
from ..lineage import LineageTracker, Span


@dataclass
class NodeExecution:
    """节点执行记录"""
    node_id: str
    run_id: str
    status: ExecutionStatus
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    lineage_span_id: Optional[str] = None


@dataclass
class ExecutionResult:
    """执行结果"""
    workflow_id: str
    run_id: str
    status: ExecutionStatus
    start_time: float
    end_time: Optional[float]
    context: WorkflowContext
    node_executions: Dict[str, NodeExecution]
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """执行时长"""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def success_count(self) -> int:
        """成功节点数"""
        return sum(
            1 for exec_ in self.node_executions.values()
            if exec_.status == ExecutionStatus.COMPLETED
        )
    
    @property
    def failed_count(self) -> int:
        """失败节点数"""
        return sum(
            1 for exec_ in self.node_executions.values()
            if exec_.status == ExecutionStatus.FAILED
        )


class WorkflowExecutor:
    """工作流执行器"""
    
    def __init__(self, workflow: Workflow, lineage_tracker: Optional[LineageTracker] = None):
        self.workflow = workflow
        self.lineage_tracker = lineage_tracker or LineageTracker()
        self._running: bool = False
        self._node_executions: Dict[str, NodeExecution] = {}
    
    async def execute(self, initial_context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """执行工作流"""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        
        # 创建上下文
        context = WorkflowContext(
            workflow_id=self.workflow.workflow_id,
            run_id=run_id,
            variables=initial_context or {},
        )
        
        # 开始 Lineage 追踪
        self.lineage_tracker.start_workflow(
            run_id=run_id,
            workflow_name=self.workflow.name,
            initial_context=initial_context or {},
        )
        
        result = ExecutionResult(
            workflow_id=self.workflow.workflow_id,
            run_id=run_id,
            status=ExecutionStatus.RUNNING,
            start_time=start_time,
            end_time=None,
            context=context,
            node_executions=self._node_executions,
        )
        
        try:
            # 验证工作流
            errors = self.workflow.validate()
            if errors:
                raise ValueError(f"Workflow validation failed: {errors}")
            
            self._running = True
            
            # 执行
            await self._execute_nodes(context)
            
            result.status = ExecutionStatus.COMPLETED
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            
            # 记录失败
            self.lineage_tracker.end_workflow(
                run_id=run_id,
                success=False,
                error=str(e),
            )
            raise
        finally:
            result.end_time = time.time()
            self._running = False
            
            # 结束 Lineage 追踪
            if result.status == ExecutionStatus.COMPLETED:
                self.lineage_tracker.end_workflow(
                    run_id=run_id,
                    success=True,
                    final_context=context.variables,
                )
        
        return result
    
    async def _execute_nodes(self, context: WorkflowContext) -> None:
        """执行节点"""
        # 准备就绪队列
        ready_queue: deque[str] = deque()
        completed: Set[str] = set()
        in_progress: Set[str] = set()
        
        # 从入口点开始
        if self.workflow.entry_point:
            ready_queue.append(self.workflow.entry_point)
        
        while ready_queue and self._running:
            # 检查是否可以并行执行
            parallel_nodes: List[str] = []
            while ready_queue:
                node_id = ready_queue.popleft()
                
                # 检查所有前驱是否已完成
                predecessors = self.workflow.get_predecessors(node_id)
                if all(pred in completed for pred in predecessors):
                    parallel_nodes.append(node_id)
            
            if not parallel_nodes:
                # 没有可执行的节点
                break
            
            # 并行执行节点
            tasks = [
                self._execute_node(node_id, context)
                for node_id in parallel_nodes
            ]
            
            in_progress = set(parallel_nodes)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            in_progress.clear()
            
            # 处理结果
            for node_id, result in zip(parallel_nodes, results):
                if isinstance(result, Exception):
                    # 节点执行失败
                    raise result
                completed.add(node_id)
                
                # 添加后继节点到就绪队列
                for edge in self.workflow.get_outgoing_edges(node_id):
                    # 检查条件
                    if edge.condition and not edge.condition(context):
                        continue
                    if edge.to_node not in ready_queue and edge.to_node not in in_progress:
                        ready_queue.append(edge.to_node)
    
    async def _execute_node(self, node_id: str, context: WorkflowContext) -> Any:
        """执行单个节点"""
        node = self.workflow.nodes[node_id]
        
        # 创建执行记录
        execution = NodeExecution(
            node_id=node_id,
            run_id=context.run_id,
            status=ExecutionStatus.RUNNING,
        )
        self._node_executions[node_id] = execution
        
        # 开始 Lineage Span
        span = self.lineage_tracker.start_node(
            run_id=context.run_id,
            node_id=node_id,
            node_name=node.name,
            node_type=node.node_type.value,
            config=node.config,
        )
        execution.lineage_span_id = span.span_id
        
        try:
            # 应用输入映射
            inputs = self._apply_input_mapping(node, context)
            
            # 记录输入
            self.lineage_tracker.record_node_inputs(
                span_id=span.span_id,
                inputs=inputs,
            )
            
            # 执行节点处理
            result = await self._execute_with_retry(node, inputs, context)
            
            # 应用输出映射
            self._apply_output_mapping(node, result, context)
            
            # 记录输出
            self.lineage_tracker.record_node_outputs(
                span_id=span.span_id,
                outputs=result if isinstance(result, dict) else {"result": result},
            )
            
            execution.status = ExecutionStatus.COMPLETED
            execution.result = result
            
            return result
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            
            # 记录错误
            self.lineage_tracker.end_node(
                span_id=span.span_id,
                success=False,
                error=str(e),
            )
            raise
        finally:
            execution.end_time = time.time()
            
            # 结束 Span（如果还没结束）
            if execution.status == ExecutionStatus.COMPLETED:
                self.lineage_tracker.end_node(
                    span_id=span.span_id,
                    success=True,
                )
    
    async def _execute_with_retry(self, node: WorkflowNode, inputs: Dict[str, Any],
                                   context: WorkflowContext) -> Any:
        """带重试的执行"""
        max_retries = node.retry_config.get("max_retries", 3)
        retry_delay = node.retry_config.get("retry_delay", 1.0)
        backoff_factor = node.retry_config.get("backoff_factor", 2.0)
        
        last_error: Optional[Exception] = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self._call_handler(node, inputs, context)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (backoff_factor ** attempt))
                    continue
                raise
        
        raise last_error or Exception("Unknown error")
    
    async def _call_handler(self, node: WorkflowNode, inputs: Dict[str, Any],
                             context: WorkflowContext) -> Any:
        """调用节点处理器"""
        if node.handler:
            # 自定义处理器
            if asyncio.iscoroutinefunction(node.handler):
                return await node.handler(inputs, context)
            else:
                return node.handler(inputs, context)
        else:
            # 默认处理
            return await self._default_handler(node, inputs, context)
    
    async def _default_handler(self, node: WorkflowNode, inputs: Dict[str, Any],
                                context: WorkflowContext) -> Any:
        """默认处理器"""
        if node.node_type == NodeType.MODEL:
            return await self._handle_model_node(node, inputs, context)
        elif node.node_type == NodeType.AGENT:
            return await self._handle_agent_node(node, inputs, context)
        elif node.node_type == NodeType.TOOL:
            return await self._handle_tool_node(node, inputs, context)
        elif node.node_type == NodeType.PARALLEL:
            return await self._handle_parallel_node(node, inputs, context)
        elif node.node_type == NodeType.AGGREGATE:
            return await self._handle_aggregate_node(node, inputs, context)
        else:
            # 通过节点
            return inputs
    
    def _apply_input_mapping(self, node: WorkflowNode, context: WorkflowContext) -> Dict[str, Any]:
        """应用输入映射"""
        if not node.input_mapping:
            return dict(context.variables)
        
        result = {}
        for source_key, target_key in node.input_mapping.items():
            if source_key in context.variables:
                result[target_key] = context.variables[source_key]
        return result
    
    def _apply_output_mapping(self, node: WorkflowNode, result: Any, context: WorkflowContext) -> None:
        """应用输出映射"""
        if not isinstance(result, dict):
            result = {"result": result}
        
        if not node.output_mapping:
            context.merge(result)
            return
        
        for source_key, target_key in node.output_mapping.items():
            if source_key in result:
                context.set(target_key, result[source_key])
    
    async def _handle_model_node(self, node: WorkflowNode, inputs: Dict[str, Any],
                                  context: WorkflowContext) -> Dict[str, Any]:
        """处理模型节点"""
        # 这里可以集成实际的模型调用
        model_name = node.config.get("model_name", "default")
        prompt = inputs.get("prompt", "")
        
        # 记录 Token 统计
        self.lineage_tracker.record_token_usage(
            span_id=self._node_executions[node.node_id].lineage_span_id,
            prompt_tokens=len(prompt.split()),
            completion_tokens=0,  # 模拟
            total_tokens=len(prompt.split()),
        )
        
        return {
            "model": model_name,
            "input": prompt,
            "output": f"Generated response for: {prompt[:50]}...",
        }
    
    async def _handle_agent_node(self, node: WorkflowNode, inputs: Dict[str, Any],
                                  context: WorkflowContext) -> Dict[str, Any]:
        """处理 Agent 节点"""
        agent_role = node.config.get("role", "assistant")
        task = inputs.get("task", "")
        
        # 记录 Agent 信息
        self.lineage_tracker.record_agent_info(
            span_id=self._node_executions[node.node_id].lineage_span_id,
            agent_role=agent_role,
            agent_config=node.config,
        )
        
        return {
            "agent_role": agent_role,
            "task": task,
            "result": f"Agent {agent_role} completed task: {task[:50]}...",
        }
    
    async def _handle_tool_node(self, node: WorkflowNode, inputs: Dict[str, Any],
                                 context: WorkflowContext) -> Dict[str, Any]:
        """处理工具节点"""
        tool_name = node.config.get("tool_name", "unknown")
        tool_args = inputs.get("args", {})
        
        # 记录工具调用
        self.lineage_tracker.record_tool_call(
            span_id=self._node_executions[node.node_id].lineage_span_id,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result={"status": "success"},
        )
        
        return {
            "tool": tool_name,
            "args": tool_args,
            "result": f"Tool {tool_name} executed successfully",
        }
    
    async def _handle_parallel_node(self, node: WorkflowNode, inputs: Dict[str, Any],
                                     context: WorkflowContext) -> Dict[str, Any]:
        """处理并行节点"""
        branches = node.config.get("branches", [])
        
        async def execute_branch(branch: str) -> Any:
            return {"branch": branch, "result": f"Branch {branch} executed"}
        
        results = await asyncio.gather(*[execute_branch(b) for b in branches])
        return {"parallel_results": results}
    
    async def _handle_aggregate_node(self, node: WorkflowNode, inputs: Dict[str, Any],
                                      context: WorkflowContext) -> Dict[str, Any]:
        """处理聚合节点"""
        aggregate_type = node.config.get("aggregate_type", "merge")
        
        if aggregate_type == "merge":
            return {"merged": inputs}
        elif aggregate_type == "join":
            separator = node.config.get("separator", "\n")
            return {"joined": separator.join(map(str, inputs.values()))}
        else:
            return {"aggregated": inputs}


class ParallelExecutor:
    """并行工作流执行器"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_multiple(self, workflows: List[Workflow],
                                 contexts: Optional[List[Dict[str, Any]]] = None) -> List[ExecutionResult]:
        """并行执行多个工作流"""
        if contexts is None:
            contexts = [{} for _ in workflows]
        
        async def execute_with_semaphore(workflow: Workflow, ctx: Dict[str, Any]) -> ExecutionResult:
            async with self._semaphore:
                executor = WorkflowExecutor(workflow)
                return await executor.execute(ctx)
        
        tasks = [
            execute_with_semaphore(wf, ctx)
            for wf, ctx in zip(workflows, contexts)
        ]
        
        return await asyncio.gather(*tasks)
