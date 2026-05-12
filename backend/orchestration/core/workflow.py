"""
工作流定义与数据结构
Workflow Definition & Data Structures
"""

from __future__ import annotations

import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union


class NodeType(Enum):
    """节点类型"""
    START = "start"
    END = "end"
    MODEL = "model"
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    AGGREGATE = "aggregate"


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class WorkflowContext:
    """工作流执行上下文"""
    workflow_id: str
    run_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    def set(self, key: str, value: Any) -> None:
        """设置变量"""
        self.variables[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(key, default)
    
    def merge(self, data: Dict[str, Any]) -> None:
        """合并变量"""
        self.variables.update(data)


@dataclass
class WorkflowNode:
    """工作流节点"""
    node_id: str
    name: str
    node_type: NodeType
    config: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_mapping: Dict[str, str] = field(default_factory=dict)
    retry_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_retries": 3,
        "retry_delay": 1.0,
        "backoff_factor": 2.0,
    })
    timeout: float = 300.0  # 5分钟超时
    
    @classmethod
    def create(cls, name: str, node_type: NodeType, **kwargs) -> WorkflowNode:
        """创建节点"""
        node_id = kwargs.pop("node_id", f"node_{uuid.uuid4().hex[:8]}")
        return cls(node_id=node_id, name=name, node_type=node_type, **kwargs)


@dataclass
class WorkflowEdge:
    """工作流边（节点连接关系）"""
    from_node: str
    to_node: str
    condition: Optional[Callable[[WorkflowContext], bool]] = None
    condition_label: Optional[str] = None
    
    @classmethod
    def create(cls, from_node: str, to_node: str, condition: Optional[Callable] = None,
               condition_label: Optional[str] = None) -> WorkflowEdge:
        """创建边"""
        return cls(from_node=from_node, to_node=to_node,
                   condition=condition, condition_label=condition_label)


class Workflow:
    """工作流定义"""
    
    def __init__(self, name: str, description: str = "", workflow_id: Optional[str] = None):
        self.workflow_id = workflow_id or f"wf_{uuid.uuid4().hex[:12]}"
        self.name = name
        self.description = description
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
        self.entry_point: Optional[str] = None
        self.exit_points: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def add_node(self, node: WorkflowNode) -> Workflow:
        """添加节点"""
        self.nodes[node.node_id] = node
        self.updated_at = time.time()
        return self
    
    def add_nodes(self, nodes: List[WorkflowNode]) -> Workflow:
        """批量添加节点"""
        for node in nodes:
            self.nodes[node.node_id] = node
        self.updated_at = time.time()
        return self
    
    def add_edge(self, edge: WorkflowEdge) -> Workflow:
        """添加边"""
        self.edges.append(edge)
        self.updated_at = time.time()
        return self
    
    def add_edges(self, edges: List[WorkflowEdge]) -> Workflow:
        """批量添加边"""
        self.edges.extend(edges)
        self.updated_at = time.time()
        return self
    
    def connect(self, from_node_id: str, to_node_id: str,
                condition: Optional[Callable] = None,
                condition_label: Optional[str] = None) -> Workflow:
        """快捷连接两个节点"""
        edge = WorkflowEdge.create(
            from_node=from_node_id,
            to_node=to_node_id,
            condition=condition,
            condition_label=condition_label,
        )
        return self.add_edge(edge)
    
    def set_entry_point(self, node_id: str) -> Workflow:
        """设置入口点"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in workflow")
        self.entry_point = node_id
        return self
    
    def add_exit_point(self, node_id: str) -> Workflow:
        """添加退出点"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in workflow")
        if node_id not in self.exit_points:
            self.exit_points.append(node_id)
        return self
    
    def get_successors(self, node_id: str) -> List[str]:
        """获取节点的后继节点"""
        return [edge.to_node for edge in self.edges if edge.from_node == node_id]
    
    def get_predecessors(self, node_id: str) -> List[str]:
        """获取节点的前驱节点"""
        return [edge.from_node for edge in self.edges if edge.to_node == node_id]
    
    def get_outgoing_edges(self, node_id: str) -> List[WorkflowEdge]:
        """获取节点的出边"""
        return [edge for edge in self.edges if edge.from_node == node_id]
    
    def validate(self) -> List[str]:
        """验证工作流定义"""
        errors: List[str] = []
        
        # 检查入口点
        if not self.entry_point:
            errors.append("Workflow must have an entry point")
        
        # 检查节点引用
        all_node_ids = set(self.nodes.keys())
        for edge in self.edges:
            if edge.from_node not in all_node_ids:
                errors.append(f"Edge references non-existent from_node: {edge.from_node}")
            if edge.to_node not in all_node_ids:
                errors.append(f"Edge references non-existent to_node: {edge.to_node}")
        
        # 检查循环（简单 DAG 检查）
        if not self._is_dag():
            errors.append("Workflow contains cycles")
        
        # 检查孤立节点
        reachable = self._get_reachable_nodes()
        for node_id in all_node_ids:
            if node_id != self.entry_point and node_id not in reachable:
                errors.append(f"Node {node_id} is unreachable from entry point")
        
        return errors
    
    def _is_dag(self) -> bool:
        """检查是否是有向无环图"""
        if not self.nodes:
            return True
        
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for successor in self.get_successors(node_id):
                if successor not in visited:
                    if has_cycle(successor):
                        return True
                elif successor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    return False
        
        return True
    
    def _get_reachable_nodes(self) -> set:
        """获取从入口点可达的所有节点"""
        if not self.entry_point:
            return set()
        
        reachable = set()
        stack = [self.entry_point]
        
        while stack:
            node = stack.pop()
            if node not in reachable:
                reachable.add(node)
                stack.extend(self.get_successors(node))
        
        return reachable
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化工作流"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "name": node.name,
                    "node_type": node.node_type.value,
                    "config": node.config,
                    "input_mapping": node.input_mapping,
                    "output_mapping": node.output_mapping,
                    "retry_config": node.retry_config,
                    "timeout": node.timeout,
                }
                for node_id, node in self.nodes.items()
            },
            "edges": [
                {
                    "from_node": edge.from_node,
                    "to_node": edge.to_node,
                    "condition_label": edge.condition_label,
                }
                for edge in self.edges
            ],
            "entry_point": self.entry_point,
            "exit_points": self.exit_points,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Workflow:
        """反序列化工作流"""
        wf = cls(
            name=data["name"],
            description=data.get("description", ""),
            workflow_id=data["workflow_id"],
        )
        
        # 重建节点
        for node_id, node_data in data["nodes"].items():
            node = WorkflowNode(
                node_id=node_data["node_id"],
                name=node_data["name"],
                node_type=NodeType(node_data["node_type"]),
                config=node_data.get("config", {}),
                input_mapping=node_data.get("input_mapping", {}),
                output_mapping=node_data.get("output_mapping", {}),
                retry_config=node_data.get("retry_config", {"max_retries": 3}),
                timeout=node_data.get("timeout", 300.0),
            )
            wf.add_node(node)
        
        # 重建边（注意：条件函数无法序列化，需要单独处理）
        for edge_data in data["edges"]:
            edge = WorkflowEdge(
                from_node=edge_data["from_node"],
                to_node=edge_data["to_node"],
                condition_label=edge_data.get("condition_label"),
            )
            wf.add_edge(edge)
        
        wf.entry_point = data.get("entry_point")
        wf.exit_points = data.get("exit_points", [])
        wf.metadata = data.get("metadata", {})
        wf.created_at = data.get("created_at", time.time())
        wf.updated_at = data.get("updated_at", time.time())
        
        return wf
