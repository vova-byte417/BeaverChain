"""
Lineage 查询模块
Lineage Query Module
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta

from .tracker import LineageRecord
from .storage import LineageStorage


class QueryOperator(Enum):
    """查询操作符"""
    EQ = "eq"  # 等于
    NE = "ne"  # 不等于
    GT = "gt"  # 大于
    LT = "lt"  # 小于
    GTE = "gte"  # 大于等于
    LTE = "lte"  # 小于等于
    IN = "in"  # 包含于
    NOT_IN = "not_in"  # 不包含于
    LIKE = "like"  # 模糊匹配


@dataclass
class QueryFilter:
    """查询过滤器"""
    field: str
    operator: QueryOperator
    value: Any
    
    def evaluate(self, record: LineageRecord) -> bool:
        """评估过滤器"""
        # 获取字段值
        field_value = self._get_field_value(record)
        
        if self.operator == QueryOperator.EQ:
            return field_value == self.value
        elif self.operator == QueryOperator.NE:
            return field_value != self.value
        elif self.operator == QueryOperator.GT:
            try:
                return float(field_value) > float(self.value)
            except (TypeError, ValueError):
                return False
        elif self.operator == QueryOperator.LT:
            try:
                return float(field_value) < float(self.value)
            except (TypeError, ValueError):
                return False
        elif self.operator == QueryOperator.GTE:
            try:
                return float(field_value) >= float(self.value)
            except (TypeError, ValueError):
                return False
        elif self.operator == QueryOperator.LTE:
            try:
                return float(field_value) <= float(self.value)
            except (TypeError, ValueError):
                return False
        elif self.operator == QueryOperator.IN:
            return field_value in self.value
        elif self.operator == QueryOperator.NOT_IN:
            return field_value not in self.value
        elif self.operator == QueryOperator.LIKE:
            return str(self.value).lower() in str(field_value).lower()
        return False
    
    def _get_field_value(self, record: LineageRecord) -> Any:
        """获取字段值"""
        # 支持嵌套字段（用 . 分隔）
        parts = self.field.split(".")
        value: Any = record
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            elif isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value


class LineageQuery:
    """Lineage 查询构建器"""
    
    def __init__(self, storage: LineageStorage):
        self.storage = storage
        self._filters: List[QueryFilter] = []
        self._sort_field: Optional[str] = None
        self._sort_desc: bool = True
        self._limit: int = 100
        self._offset: int = 0
    
    def filter(self, field: str, operator: QueryOperator, value: Any) -> LineageQuery:
        """添加过滤器"""
        self._filters.append(QueryFilter(field=field, operator=operator, value=value))
        return self
    
    def filter_workflow_name(self, name: str, exact: bool = False) -> LineageQuery:
        """按工作流名称过滤"""
        op = QueryOperator.EQ if exact else QueryOperator.LIKE
        return self.filter("workflow_name", op, name)
    
    def filter_success(self, success: bool = True) -> LineageQuery:
        """按成功状态过滤"""
        return self.filter("success", QueryOperator.EQ, success)
    
    def filter_time_range(self, start: Optional[datetime] = None,
                           end: Optional[datetime] = None) -> LineageQuery:
        """按时间范围过滤"""
        if start:
            self._filters.append(QueryFilter(
                field="start_time",
                operator=QueryOperator.GTE,
                value=start.timestamp(),
            ))
        if end:
            self._filters.append(QueryFilter(
                field="start_time",
                operator=QueryOperator.LTE,
                value=end.timestamp(),
            ))
        return self
    
    def filter_last(self, hours: int = 24) -> LineageQuery:
        """过滤最近时间内的记录"""
        cutoff = time.time() - (hours * 3600)
        self._filters.append(QueryFilter(
            field="start_time",
            operator=QueryOperator.GTE,
            value=cutoff,
        ))
        return self
    
    def filter_min_duration(self, ms: float) -> LineageQuery:
        """按最小持续时间过滤"""
        return self.filter("duration_ms", QueryOperator.GTE, ms)
    
    def filter_max_duration(self, ms: float) -> LineageQuery:
        """按最大持续时间过滤"""
        return self.filter("duration_ms", QueryOperator.LTE, ms)
    
    def filter_min_tokens(self, tokens: int) -> LineageQuery:
        """按最小 Token 数过滤"""
        return self.filter("total_tokens.total_tokens", QueryOperator.GTE, tokens)
    
    def filter_has_error(self) -> LineageQuery:
        """过滤有错误的记录"""
        return self.filter("error", QueryOperator.NE, None)
    
    def filter_node_count(self, min_count: int) -> LineageQuery:
        """按最小节点数过滤"""
        return self.filter("node_count", QueryOperator.GTE, min_count)
    
    def sort_by(self, field: str, descending: bool = True) -> LineageQuery:
        """排序"""
        self._sort_field = field
        self._sort_desc = descending
        return self
    
    def limit(self, n: int) -> LineageQuery:
        """限制数量"""
        self._limit = n
        return self
    
    def offset(self, n: int) -> LineageQuery:
        """偏移量"""
        self._offset = n
        return self
    
    def execute(self) -> List[LineageRecord]:
        """执行查询"""
        # 获取所有记录（实际生产中应该使用更高效的过滤）
        all_records = self.storage.list(limit=10000, offset=0)
        
        # 应用过滤器
        filtered = [
            record for record in all_records
            if all(f.evaluate(record) for f in self._filters)
        ]
        
        # 排序
        if self._sort_field:
            filtered.sort(
                key=lambda r: self._get_sort_value(r, self._sort_field),
                reverse=self._sort_desc,
            )
        
        # 应用偏移和限制
        return filtered[self._offset:self._offset + self._limit]
    
    def _get_sort_value(self, record: LineageRecord, field: str) -> Any:
        """获取排序值"""
        parts = field.split(".")
        value: Any = record
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            elif isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return 0
        
        return value or 0
    
    def count(self) -> int:
        """获取符合条件的记录数"""
        return len(self.execute())
    
    def first(self) -> Optional[LineageRecord]:
        """获取第一条记录"""
        results = self.limit(1).execute()
        return results[0] if results else None
    
    def aggregate(self) -> Dict[str, Any]:
        """聚合统计"""
        records = self.execute()
        
        if not records:
            return {
                "count": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "total_tokens": 0,
                "success_rate": 0,
            }
        
        total_duration = sum(r.duration_ms for r in records)
        total_tokens = sum(r.total_tokens.total_tokens for r in records)
        success_count = sum(1 for r in records if r.success)
        
        return {
            "count": len(records),
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / len(records),
            "min_duration_ms": min(r.duration_ms for r in records),
            "max_duration_ms": max(r.duration_ms for r in records),
            "total_tokens": total_tokens,
            "avg_tokens": total_tokens / len(records),
            "success_count": success_count,
            "fail_count": len(records) - success_count,
            "success_rate": success_count / len(records),
        }
    
    def group_by(self, field: str) -> Dict[Any, List[LineageRecord]]:
        """按字段分组"""
        records = self.execute()
        groups: Dict[Any, List[LineageRecord]] = {}
        
        for record in records:
            key = self._get_sort_value(record, field)
            if key not in groups:
                groups[key] = []
            groups[key].append(record)
        
        return groups
