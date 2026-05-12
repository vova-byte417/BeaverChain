"""
Lineage 追踪器
Lineage Tracker
"""

from __future__ import annotations

import uuid
import time
import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set
from datetime import datetime


class MetricType(Enum):
    """指标类型"""
    TOKEN_USAGE = "token_usage"
    LATENCY = "latency"
    MEMORY = "memory"
    COST = "cost"
    SUCCESS_RATE = "success_rate"


@dataclass
class TokenStats:
    """Token 统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def add(self, other: TokenStats) -> TokenStats:
        """累加统计"""
        return TokenStats(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


@dataclass
class LatencyStats:
    """延迟统计"""
    min_ms: float = 0.0
    max_ms: float = 0.0
    avg_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    total_ms: float = 0.0
    count: int = 0


@dataclass
class Span:
    """追踪 Span - 表示一个操作的时间范围"""
    span_id: str
    parent_span_id: Optional[str]
    run_id: str
    name: str
    span_type: str  # workflow, node, tool, model, agent
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status: str = "running"  # running, completed, failed
    token_stats: TokenStats = field(default_factory=TokenStats)
    
    @property
    def duration_ms(self) -> float:
        """持续时间（毫秒）"""
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000
    
    def end(self, success: bool = True, error: Optional[str] = None) -> None:
        """结束 Span"""
        self.end_time = time.time()
        self.status = "completed" if success else "failed"
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "run_id": self.run_id,
            "name": self.name,
            "span_type": self.span_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "status": self.status,
            "error": self.error,
            "token_stats": asdict(self.token_stats) if self.token_stats else None,
        }


@dataclass
class LineageRecord:
    """完整的 Lineage 记录"""
    run_id: str
    workflow_name: str
    workflow_id: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    spans: Dict[str, Span] = field(default_factory=dict)
    initial_context: Dict[str, Any] = field(default_factory=dict)
    final_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        """总持续时间"""
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000
    
    @property
    def total_tokens(self) -> TokenStats:
        """总 Token 消耗"""
        total = TokenStats()
        for span in self.spans.values():
            total = total.add(span.token_stats)
        return total
    
    @property
    def node_count(self) -> int:
        """节点数量"""
        return sum(1 for s in self.spans.values() if s.span_type == "node")
    
    @property
    def tool_call_count(self) -> int:
        """工具调用数量"""
        return sum(1 for s in self.spans.values() if s.span_type == "tool")
    
    def get_root_span(self) -> Optional[Span]:
        """获取根 Span"""
        for span in self.spans.values():
            if span.parent_span_id is None and span.span_type == "workflow":
                return span
        return None
    
    def get_child_spans(self, parent_span_id: str) -> List[Span]:
        """获取子 Span"""
        return [s for s in self.spans.values() if s.parent_span_id == parent_span_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "run_id": self.run_id,
            "workflow_name": self.workflow_name,
            "workflow_id": self.workflow_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "spans": {k: v.to_dict() for k, v in self.spans.items()},
            "initial_context": self._sanitize_context(self.initial_context),
            "final_context": self._sanitize_context(self.final_context),
            "total_tokens": asdict(self.total_tokens),
            "node_count": self.node_count,
            "tool_call_count": self.tool_call_count,
            "metadata": self.metadata,
        }
    
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """清理上下文（避免敏感信息和过大内容）"""
        result = {}
        for key, value in context.items():
            # 跳过敏感字段
            if any(sensitive in key.lower() for sensitive in ["password", "secret", "token", "key"]):
                result[key] = "[REDACTED]"
                continue
            
            # 限制值的大小
            if isinstance(value, (str, bytes)) and len(str(value)) > 1000:
                result[key] = f"[TRUNCATED] {str(value)[:500]}..."
            else:
                result[key] = value
        return result


class LineageGraph:
    """Lineage 图 - 用于可视化和分析"""
    
    def __init__(self, record: LineageRecord):
        self.record = record
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self._build_graph()
    
    def _build_graph(self) -> None:
        """构建图"""
        # 添加节点
        for span_id, span in self.record.spans.items():
            self.nodes[span_id] = {
                "id": span_id,
                "name": span.name,
                "type": span.span_type,
                "status": span.status,
                "duration_ms": span.duration_ms,
                "token_stats": span.token_stats,
                "attributes": span.attributes,
            }
        
        # 添加边
        for span_id, span in self.record.spans.items():
            if span.parent_span_id and span.parent_span_id in self.nodes:
                self.edges.append({
                    "from": span.parent_span_id,
                    "to": span_id,
                    "relationship": "parent_child",
                })
    
    def get_critical_path(self) -> List[str]:
        """获取关键路径（耗时最长的路径）"""
        root = self.record.get_root_span()
        if not root:
            return []
        
        def longest_path(node_id: str) -> List[str]:
            node = self.nodes[node_id]
            children = [e["to"] for e in self.edges if e["from"] == node_id]
            
            if not children:
                return [node_id]
            
            paths = [longest_path(c) for c in children]
            max_path = max(paths, key=lambda p: sum(
                self.nodes[n]["duration_ms"] for n in p
            ))
            
            return [node_id] + max_path
        
        return longest_path(root.span_id)
    
    def get_bottlenecks(self, threshold_ms: float = 1000) -> List[str]:
        """获取瓶颈节点（耗时超过阈值）"""
        return [
            node_id for node_id, node in self.nodes.items()
            if node["duration_ms"] > threshold_ms and node["type"] != "workflow"
        ]
    
    def to_mermaid(self) -> str:
        """生成 Mermaid 流程图"""
        lines = ["graph TD"]
        
        # 节点样式映射
        style_map = {
            "workflow": ":::workflow",
            "node": ":::node",
            "tool": ":::tool",
            "model": ":::model",
            "agent": ":::agent",
        }
        
        status_style = {
            "completed": "fill:#90EE90,stroke:#333",
            "failed": "fill:#FFB6C1,stroke:#333",
            "running": "fill:#87CEEB,stroke:#333",
        }
        
        # 添加节点
        for node_id, node in self.nodes.items():
            label = f"{node['name']}\\n({node['duration_ms']:.1f}ms)"
            style = style_map.get(node["type"], "")
            lines.append(f"    {node_id}[\"{label}\"]{style}")
        
        # 添加边
        for edge in self.edges:
            lines.append(f"    {edge['from']} --> {edge['to']}")
        
        # 添加类定义
        lines.extend([
            "    classDef workflow fill:#E6E6FA,stroke:#333,stroke-width:2px",
            "    classDef node fill:#F0F8FF,stroke:#333",
            "    classDef tool fill:#FFF0F5,stroke:#333",
            "    classDef model fill:#F5F5DC,stroke:#333",
            "    classDef agent fill:#FFE4E1,stroke:#333",
        ])
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "critical_path": self.get_critical_path(),
            "bottlenecks": self.get_bottlenecks(),
        }


class LineageTracker:
    """Lineage 追踪器"""
    
    def __init__(self):
        self._records: Dict[str, LineageRecord] = {}
        self._active_spans: Dict[str, Span] = {}
    
    def start_workflow(self, run_id: str, workflow_name: str,
                        workflow_id: str = "", initial_context: Optional[Dict[str, Any]] = None) -> Span:
        """开始工作流追踪"""
        # 创建记录
        record = LineageRecord(
            run_id=run_id,
            workflow_name=workflow_name,
            workflow_id=workflow_id,
            initial_context=initial_context or {},
        )
        self._records[run_id] = record
        
        # 创建工作流 Span
        span = Span(
            span_id=f"wf_{run_id}",
            parent_span_id=None,
            run_id=run_id,
            name=workflow_name,
            span_type="workflow",
        )
        record.spans[span.span_id] = span
        self._active_spans[span.span_id] = span
        
        return span
    
    def end_workflow(self, run_id: str, success: bool,
                      final_context: Optional[Dict[str, Any]] = None,
                      error: Optional[str] = None) -> None:
        """结束工作流追踪"""
        record = self._records.get(run_id)
        if not record:
            return
        
        record.success = success
        record.error = error
        record.final_context = final_context or {}
        record.end_time = time.time()
        
        # 结束工作流 Span
        workflow_span = record.get_root_span()
        if workflow_span:
            workflow_span.end(success=success, error=error)
            if workflow_span.span_id in self._active_spans:
                del self._active_spans[workflow_span.span_id]
    
    def start_node(self, run_id: str, node_id: str, node_name: str,
                    node_type: str, config: Optional[Dict[str, Any]] = None,
                    parent_span_id: Optional[str] = None) -> Span:
        """开始节点追踪"""
        record = self._records.get(run_id)
        if not record:
            # 如果记录不存在，创建一个（容错）
            record = LineageRecord(run_id=run_id, workflow_name="unknown", workflow_id="")
            self._records[run_id] = record
        
        # 如果没有指定父 Span，使用工作流 Span
        if not parent_span_id:
            parent_span_id = f"wf_{run_id}"
        
        span = Span(
            span_id=f"node_{node_id}_{uuid.uuid4().hex[:8]}",
            parent_span_id=parent_span_id,
            run_id=run_id,
            name=node_name,
            span_type=node_type,
            attributes={"node_id": node_id, "config": config or {}},
        )
        record.spans[span.span_id] = span
        self._active_spans[span.span_id] = span
        
        return span
    
    def end_node(self, span_id: str, success: bool, error: Optional[str] = None) -> None:
        """结束节点追踪"""
        span = self._active_spans.get(span_id)
        if span:
            span.end(success=success, error=error)
            del self._active_spans[span_id]
    
    def record_node_inputs(self, span_id: str, inputs: Dict[str, Any]) -> None:
        """记录节点输入"""
        span = self._active_spans.get(span_id)
        if span:
            span.inputs = inputs
    
    def record_node_outputs(self, span_id: str, outputs: Dict[str, Any]) -> None:
        """记录节点输出"""
        span = self._active_spans.get(span_id)
        if span:
            span.outputs = outputs
    
    def record_tool_call(self, span_id: str, tool_name: str, tool_args: Dict[str, Any],
                          tool_result: Optional[Dict[str, Any]] = None,
                          parent_span_id: Optional[str] = None) -> Span:
        """记录工具调用"""
        # 查找父 Span
        parent_span = self._active_spans.get(span_id)
        if not parent_span:
            parent_span = self._active_spans.get(parent_span_id) if parent_span_id else None
        
        if not parent_span:
            # 创建一个空的父 Span
            parent_span_id = span_id
        else:
            parent_span_id = parent_span.span_id
            run_id = parent_span.run_id
            record = self._records.get(run_id)
            
            if record:
                tool_span = Span(
                    span_id=f"tool_{tool_name}_{uuid.uuid4().hex[:8]}",
                    parent_span_id=parent_span_id,
                    run_id=run_id,
                    name=tool_name,
                    span_type="tool",
                    attributes={"args": tool_args, "result": tool_result or {}},
                )
                record.spans[tool_span.span_id] = tool_span
                tool_span.end(success=True)
                return tool_span
        
        # 回退：创建一个临时 Span
        return Span(
            span_id=f"tool_{tool_name}_{uuid.uuid4().hex[:8]}",
            parent_span_id=parent_span_id or span_id,
            run_id="unknown",
            name=tool_name,
            span_type="tool",
        )
    
    def record_token_usage(self, span_id: str, prompt_tokens: int,
                            completion_tokens: int, total_tokens: int) -> None:
        """记录 Token 使用量"""
        span = self._active_spans.get(span_id)
        if span:
            span.token_stats = TokenStats(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
    
    def record_agent_info(self, span_id: str, agent_role: str, agent_config: Dict[str, Any]) -> None:
        """记录 Agent 信息"""
        span = self._active_spans.get(span_id)
        if span:
            span.attributes["agent_role"] = agent_role
            span.attributes["agent_config"] = agent_config
    
    def get_record(self, run_id: str) -> Optional[LineageRecord]:
        """获取 Lineage 记录"""
        return self._records.get(run_id)
    
    def get_graph(self, run_id: str) -> Optional[LineageGraph]:
        """获取 Lineage 图"""
        record = self._records.get(run_id)
        if record:
            return LineageGraph(record)
        return None
    
    def list_records(self, limit: int = 100, offset: int = 0) -> List[LineageRecord]:
        """列出记录"""
        records = sorted(
            self._records.values(),
            key=lambda r: r.start_time,
            reverse=True,
        )
        return records[offset:offset + limit]
    
    def get_aggregated_stats(self) -> Dict[str, Any]:
        """获取聚合统计"""
        all_tokens = TokenStats()
        total_duration = 0.0
        success_count = 0
        fail_count = 0
        
        for record in self._records.values():
            all_tokens = all_tokens.add(record.total_tokens)
            total_duration += record.duration_ms
            if record.success:
                success_count += 1
            elif record.success is False:
                fail_count += 1
        
        total_runs = len(self._records)
        success_rate = success_count / total_runs if total_runs > 0 else 0
        
        return {
            "total_runs": total_runs,
            "success_count": success_count,
            "fail_count": fail_count,
            "success_rate": success_rate,
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / total_runs if total_runs > 0 else 0,
            "total_tokens": asdict(all_tokens),
            "total_nodes_executed": sum(r.node_count for r in self._records.values()),
            "total_tool_calls": sum(r.tool_call_count for r in self._records.values()),
        }
    
    def export_record(self, run_id: str, filepath: str) -> None:
        """导出记录到文件"""
        record = self._records.get(run_id)
        if not record:
            raise ValueError(f"Record not found: {run_id}")
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)
    
    def import_record(self, filepath: str) -> LineageRecord:
        """从文件导入记录"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        record = LineageRecord(
            run_id=data["run_id"],
            workflow_name=data["workflow_name"],
            workflow_id=data.get("workflow_id", ""),
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            success=data.get("success"),
            error=data.get("error"),
            initial_context=data.get("initial_context", {}),
            final_context=data.get("final_context", {}),
            metadata=data.get("metadata", {}),
        )
        
        # 重建 Spans
        for span_id, span_data in data.get("spans", {}).items():
            token_data = span_data.get("token_stats", {})
            span = Span(
                span_id=span_data["span_id"],
                parent_span_id=span_data.get("parent_span_id"),
                run_id=span_data["run_id"],
                name=span_data["name"],
                span_type=span_data["span_type"],
                start_time=span_data["start_time"],
                end_time=span_data.get("end_time"),
                attributes=span_data.get("attributes", {}),
                status=span_data.get("status", "completed"),
                error=span_data.get("error"),
                token_stats=TokenStats(
                    prompt_tokens=token_data.get("prompt_tokens", 0),
                    completion_tokens=token_data.get("completion_tokens", 0),
                    total_tokens=token_data.get("total_tokens", 0),
                ),
            )
            record.spans[span_id] = span
        
        self._records[record.run_id] = record
        return record
