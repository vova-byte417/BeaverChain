"""
条件分支与循环支持
Condition Branches & Loop Support
"""

from __future__ import annotations

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Pattern, Union

from .workflow import WorkflowContext


class ConditionType(Enum):
    """条件类型"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    AND = "and"
    OR = "or"
    CUSTOM = "custom"


@dataclass
class Condition:
    """条件定义"""
    condition_type: ConditionType
    key: Optional[str] = None
    value: Optional[Any] = None
    sub_conditions: List[Condition] = field(default_factory=list)
    custom_func: Optional[Callable[[WorkflowContext], bool]] = None
    
    def evaluate(self, context: WorkflowContext) -> bool:
        """评估条件"""
        if self.condition_type == ConditionType.CUSTOM:
            if self.custom_func:
                return self.custom_func(context)
            return False
        
        if self.condition_type == ConditionType.AND:
            return all(c.evaluate(context) for c in self.sub_conditions)
        
        if self.condition_type == ConditionType.OR:
            return any(c.evaluate(context) for c in self.sub_conditions)
        
        # 获取变量值
        var_value = context.get(self.key) if self.key else None
        
        # 单值条件
        if self.condition_type == ConditionType.IS_TRUE:
            return bool(var_value)
        if self.condition_type == ConditionType.IS_FALSE:
            return not bool(var_value)
        if self.condition_type == ConditionType.IS_NULL:
            return var_value is None
        if self.condition_type == ConditionType.IS_NOT_NULL:
            return var_value is not None
        
        # 比较条件
        if self.condition_type == ConditionType.EQUALS:
            return var_value == self.value
        if self.condition_type == ConditionType.NOT_EQUALS:
            return var_value != self.value
        
        # 数值比较
        if self.condition_type == ConditionType.GREATER_THAN:
            try:
                return float(var_value) > float(self.value)
            except (TypeError, ValueError):
                return False
        if self.condition_type == ConditionType.LESS_THAN:
            try:
                return float(var_value) < float(self.value)
            except (TypeError, ValueError):
                return False
        
        # 包含检查
        if self.condition_type == ConditionType.CONTAINS:
            if isinstance(var_value, str) and isinstance(self.value, str):
                return self.value in var_value
            if isinstance(var_value, (list, dict)):
                return self.value in var_value
            return False
        
        if self.condition_type == ConditionType.NOT_CONTAINS:
            if isinstance(var_value, str) and isinstance(self.value, str):
                return self.value not in var_value
            if isinstance(var_value, (list, dict)):
                return self.value not in var_value
            return True
        
        # 正则匹配
        if self.condition_type == ConditionType.MATCHES:
            if isinstance(var_value, str):
                pattern = re.compile(str(self.value))
                return bool(pattern.match(var_value))
            return False
        
        return False
    
    # 工厂方法
    @classmethod
    def equals(cls, key: str, value: Any) -> Condition:
        return cls(ConditionType.EQUALS, key=key, value=value)
    
    @classmethod
    def not_equals(cls, key: str, value: Any) -> Condition:
        return cls(ConditionType.NOT_EQUALS, key=key, value=value)
    
    @classmethod
    def greater_than(cls, key: str, value: float) -> Condition:
        return cls(ConditionType.GREATER_THAN, key=key, value=value)
    
    @classmethod
    def less_than(cls, key: str, value: float) -> Condition:
        return cls(ConditionType.LESS_THAN, key=key, value=value)
    
    @classmethod
    def contains(cls, key: str, value: Any) -> Condition:
        return cls(ConditionType.CONTAINS, key=key, value=value)
    
    @classmethod
    def matches(cls, key: str, pattern: str) -> Condition:
        return cls(ConditionType.MATCHES, key=key, value=pattern)
    
    @classmethod
    def is_true(cls, key: str) -> Condition:
        return cls(ConditionType.IS_TRUE, key=key)
    
    @classmethod
    def is_false(cls, key: str) -> Condition:
        return cls(ConditionType.IS_FALSE, key=key)
    
    @classmethod
    def is_null(cls, key: str) -> Condition:
        return cls(ConditionType.IS_NULL, key=key)
    
    @classmethod
    def is_not_null(cls, key: str) -> Condition:
        return cls(ConditionType.IS_NOT_NULL, key=key)
    
    @classmethod
    def and_(cls, *conditions: Condition) -> Condition:
        return cls(ConditionType.AND, sub_conditions=list(conditions))
    
    @classmethod
    def or_(cls, *conditions: Condition) -> Condition:
        return cls(ConditionType.OR, sub_conditions=list(conditions))
    
    @classmethod
    def custom(cls, func: Callable[[WorkflowContext], bool]) -> Condition:
        return cls(ConditionType.CUSTOM, custom_func=func)
    
    def to_edge_condition(self) -> Callable[[WorkflowContext], bool]:
        """转换为边条件函数"""
        return lambda ctx: self.evaluate(ctx)


@dataclass
class LoopSpec:
    """循环规格"""
    loop_type: str  # "for", "while", "foreach"
    max_iterations: int = 100
    break_condition: Optional[Condition] = None
    
    # For 循环
    start: Optional[int] = None
    end: Optional[int] = None
    step: int = 1
    
    # ForEach 循环
    iterable_key: Optional[str] = None
    item_key: str = "item"
    index_key: str = "index"
    
    # While 循环
    while_condition: Optional[Condition] = None
    
    @classmethod
    def for_range(cls, start: int, end: int, step: int = 1,
                   max_iterations: int = 1000) -> LoopSpec:
        """创建范围循环"""
        return cls(
            loop_type="for",
            start=start,
            end=end,
            step=step,
            max_iterations=max_iterations,
        )
    
    @classmethod
    def for_each(cls, iterable_key: str, item_key: str = "item",
                  index_key: str = "index", max_iterations: int = 1000) -> LoopSpec:
        """创建 ForEach 循环"""
        return cls(
            loop_type="foreach",
            iterable_key=iterable_key,
            item_key=item_key,
            index_key=index_key,
            max_iterations=max_iterations,
        )
    
    @classmethod
    def while_(cls, condition: Condition, max_iterations: int = 100) -> LoopSpec:
        """创建 While 循环"""
        return cls(
            loop_type="while",
            while_condition=condition,
            max_iterations=max_iterations,
        )
    
    def get_iterator(self, context: WorkflowContext) -> LoopIterator:
        """获取迭代器"""
        return LoopIterator(self, context)


class LoopIterator:
    """循环迭代器"""
    
    def __init__(self, spec: LoopSpec, context: WorkflowContext):
        self.spec = spec
        self.context = context
        self.current_index = 0
        self._iterable: List[Any] = []
        self._prepare_iterator()
    
    def _prepare_iterator(self) -> None:
        """准备迭代器"""
        if self.spec.loop_type == "for":
            start = self.spec.start or 0
            end = self.spec.end or 0
            step = self.spec.step or 1
            self._iterable = list(range(start, end, step))
        
        elif self.spec.loop_type == "foreach":
            iterable_value = self.context.get(self.spec.iterable_key or "", [])
            if isinstance(iterable_value, (list, tuple)):
                self._iterable = list(iterable_value)
            elif isinstance(iterable_value, dict):
                self._iterable = list(iterable_value.items())
            else:
                self._iterable = []
    
    def __iter__(self) -> LoopIterator:
        return self
    
    def __next__(self) -> Dict[str, Any]:
        # 检查最大迭代次数
        if self.current_index >= self.spec.max_iterations:
            raise StopIteration
        
        # 检查中断条件
        if self.spec.break_condition and self.spec.break_condition.evaluate(self.context):
            raise StopIteration
        
        # For / ForEach 循环
        if self.spec.loop_type in ("for", "foreach"):
            if self.current_index >= len(self._iterable):
                raise StopIteration
            
            item = self._iterable[self.current_index]
            result = {
                self.spec.index_key: self.current_index,
                self.spec.item_key: item,
            }
            self.current_index += 1
            return result
        
        # While 循环
        elif self.spec.loop_type == "while":
            if self.current_index > 0:
                # 检查 while 条件
                if not (self.spec.while_condition and self.spec.while_condition.evaluate(self.context)):
                    raise StopIteration
            
            result = {
                self.spec.index_key: self.current_index,
            }
            self.current_index += 1
            return result
        
        raise StopIteration
    
    @property
    def has_more(self) -> bool:
        """是否还有更多迭代"""
        if self.current_index >= self.spec.max_iterations:
            return False
        
        if self.spec.break_condition and self.spec.break_condition.evaluate(self.context):
            return False
        
        if self.spec.loop_type in ("for", "foreach"):
            return self.current_index < len(self._iterable)
        
        if self.spec.loop_type == "while":
            return self.spec.while_condition and self.spec.while_condition.evaluate(self.context)
        
        return False
