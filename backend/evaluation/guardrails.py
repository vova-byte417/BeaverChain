"""Guardrails: 输入/输出过滤规则引擎 + 审计日志."""

from __future__ import annotations

import re
import time
import uuid
import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Pattern


class RuleType(Enum):
    REGEX = "regex"
    KEYWORD = "keyword"
    LENGTH_MAX = "length_max"
    LENGTH_MIN = "length_min"
    PII = "pii"
    TOXICITY = "toxicity"
    PROMPT_INJECTION = "prompt_injection"
    CUSTOM = "custom"


class RuleAction(Enum):
    BLOCK = "block"           # 阻止请求
    REDACT = "redact"         # 脱敏（替换为 ***）
    WARN = "warn"             # 通过但记录警告
    REWRITE = "rewrite"       # 调用 rewriter 改写
    LOG_ONLY = "log_only"


@dataclass
class GuardrailRule:
    rule_id: str
    name: str
    rule_type: RuleType
    action: RuleAction
    pattern: Optional[str] = None       # regex/keyword
    threshold: Optional[float] = None   # length/toxicity 阈值
    severity: str = "medium"            # low / medium / high / critical
    apply_to: str = "both"              # input / output / both
    custom_fn: Optional[Callable[[str], bool]] = None
    rewriter: Optional[Callable[[str], str]] = None
    enabled: bool = True

    @classmethod
    def regex(cls, name: str, pattern: str, action: RuleAction = RuleAction.BLOCK,
              **kwargs) -> "GuardrailRule":
        return cls(rule_id=kwargs.pop("rule_id", f"rule_{uuid.uuid4().hex[:8]}"),
                   name=name, rule_type=RuleType.REGEX, action=action,
                   pattern=pattern, **kwargs)

    @classmethod
    def keyword(cls, name: str, keywords: List[str], action: RuleAction = RuleAction.BLOCK,
                **kwargs) -> "GuardrailRule":
        pattern = "|".join(re.escape(k) for k in keywords)
        return cls(rule_id=kwargs.pop("rule_id", f"rule_{uuid.uuid4().hex[:8]}"),
                   name=name, rule_type=RuleType.KEYWORD, action=action,
                   pattern=pattern, **kwargs)

    @classmethod
    def pii(cls, name: str = "PII detector", action: RuleAction = RuleAction.REDACT,
            **kwargs) -> "GuardrailRule":
        # 邮箱 / 手机号 / 身份证 / 信用卡
        pattern = (r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"                  # email
                   r"|\b1[3-9]\d{9}\b"                              # CN mobile
                   r"|\b\d{15}|\d{18}\b"                            # CN ID card
                   r"|\b(?:\d{4}[\s-]?){3}\d{4}\b")                 # credit card
        return cls(rule_id=kwargs.pop("rule_id", f"rule_{uuid.uuid4().hex[:8]}"),
                   name=name, rule_type=RuleType.PII, action=action,
                   pattern=pattern, severity="high", **kwargs)

    @classmethod
    def prompt_injection(cls, name: str = "Prompt injection",
                         action: RuleAction = RuleAction.BLOCK, **kwargs) -> "GuardrailRule":
        patterns = [
            r"ignore (?:previous|all|the above) instructions",
            r"disregard (?:the|your|all) (?:system )?prompt",
            r"you are now (?:a|an)",
            r"忽略(?:之前|以上|所有)(?:的)?指令",
            r"扮演.{0,10}(?:角色|身份)",
        ]
        return cls(rule_id=kwargs.pop("rule_id", f"rule_{uuid.uuid4().hex[:8]}"),
                   name=name, rule_type=RuleType.PROMPT_INJECTION, action=action,
                   pattern="|".join(patterns), severity="critical",
                   apply_to=kwargs.pop("apply_to", "input"), **kwargs)

    @classmethod
    def length(cls, name: str, max_chars: Optional[int] = None,
               min_chars: Optional[int] = None, action: RuleAction = RuleAction.BLOCK,
               **kwargs) -> "GuardrailRule":
        if max_chars is not None:
            return cls(rule_id=kwargs.pop("rule_id", f"rule_{uuid.uuid4().hex[:8]}"),
                       name=name, rule_type=RuleType.LENGTH_MAX, action=action,
                       threshold=float(max_chars), **kwargs)
        return cls(rule_id=kwargs.pop("rule_id", f"rule_{uuid.uuid4().hex[:8]}"),
                   name=name, rule_type=RuleType.LENGTH_MIN, action=action,
                   threshold=float(min_chars or 0), **kwargs)


@dataclass
class GuardrailViolation:
    violation_id: str
    rule_id: str
    rule_name: str
    rule_type: str
    action: str
    severity: str
    matched_content: str
    direction: str           # "input" / "output"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GuardrailDecision:
    allowed: bool
    content: str             # 经过 redact/rewrite 后的内容
    violations: List[GuardrailViolation] = field(default_factory=list)
    blocked_by: Optional[str] = None  # rule_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "content": self.content,
            "violations": [v.to_dict() for v in self.violations],
            "blocked_by": self.blocked_by,
        }


class AuditLog:
    """违规审计日志：内存 + 可选文件持久化。"""

    def __init__(self, file_path: Optional[str] = None, max_in_memory: int = 5000):
        self._records: List[GuardrailViolation] = []
        self._file_path = file_path
        self._max_in_memory = max_in_memory

    def append(self, violation: GuardrailViolation) -> None:
        self._records.append(violation)
        if len(self._records) > self._max_in_memory:
            self._records = self._records[-self._max_in_memory:]
        if self._file_path:
            with open(self._file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(violation.to_dict(), ensure_ascii=False) + "\n")

    def list(self, limit: int = 100, severity: Optional[str] = None,
             rule_id: Optional[str] = None) -> List[GuardrailViolation]:
        items = self._records
        if severity:
            items = [v for v in items if v.severity == severity]
        if rule_id:
            items = [v for v in items if v.rule_id == rule_id]
        return list(reversed(items))[:limit]

    def stats(self) -> Dict[str, Any]:
        by_severity: Dict[str, int] = {}
        by_rule: Dict[str, int] = {}
        for v in self._records:
            by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
            by_rule[v.rule_name] = by_rule.get(v.rule_name, 0) + 1
        return {
            "total": len(self._records),
            "by_severity": by_severity,
            "by_rule": by_rule,
        }


class GuardrailEngine:
    """规则引擎：按规则数组顺序应用，命中即按 action 处理。"""

    def __init__(self, rules: Optional[List[GuardrailRule]] = None,
                 audit_log: Optional[AuditLog] = None):
        self.rules: List[GuardrailRule] = rules or []
        self.audit_log = audit_log or AuditLog()
        self._compiled: Dict[str, Pattern] = {}
        self._compile_rules()

    def _compile_rules(self) -> None:
        for r in self.rules:
            if r.pattern and r.rule_type in (RuleType.REGEX, RuleType.KEYWORD,
                                             RuleType.PII, RuleType.PROMPT_INJECTION):
                try:
                    self._compiled[r.rule_id] = re.compile(r.pattern, re.IGNORECASE)
                except re.error:
                    pass

    def add_rule(self, rule: GuardrailRule) -> "GuardrailEngine":
        self.rules.append(rule)
        self._compile_rules()
        return self

    def evaluate(self, content: str, direction: str = "input") -> GuardrailDecision:
        decision = GuardrailDecision(allowed=True, content=content)

        for rule in self.rules:
            if not rule.enabled:
                continue
            if rule.apply_to not in ("both", direction):
                continue

            matched = self._match(rule, decision.content)
            if not matched:
                continue

            violation = GuardrailViolation(
                violation_id=f"v_{uuid.uuid4().hex[:10]}",
                rule_id=rule.rule_id,
                rule_name=rule.name,
                rule_type=rule.rule_type.value,
                action=rule.action.value,
                severity=rule.severity,
                matched_content=str(matched)[:200],
                direction=direction,
            )
            decision.violations.append(violation)
            self.audit_log.append(violation)

            if rule.action == RuleAction.BLOCK:
                decision.allowed = False
                decision.blocked_by = rule.rule_id
                return decision
            if rule.action == RuleAction.REDACT:
                decision.content = self._redact(rule, decision.content)
            elif rule.action == RuleAction.REWRITE and rule.rewriter:
                decision.content = rule.rewriter(decision.content)
            # WARN / LOG_ONLY: 仅记录

        return decision

    def evaluate_io(self, input_text: str, output_text: str) -> Dict[str, GuardrailDecision]:
        return {
            "input": self.evaluate(input_text, "input"),
            "output": self.evaluate(output_text, "output"),
        }

    def _match(self, rule: GuardrailRule, content: str) -> Any:
        if rule.rule_type in (RuleType.REGEX, RuleType.KEYWORD,
                              RuleType.PII, RuleType.PROMPT_INJECTION):
            pattern = self._compiled.get(rule.rule_id)
            if pattern:
                m = pattern.findall(content)
                return m if m else None
        elif rule.rule_type == RuleType.LENGTH_MAX:
            if rule.threshold is not None and len(content) > rule.threshold:
                return f"length={len(content)} > {rule.threshold}"
        elif rule.rule_type == RuleType.LENGTH_MIN:
            if rule.threshold is not None and len(content) < rule.threshold:
                return f"length={len(content)} < {rule.threshold}"
        elif rule.rule_type == RuleType.CUSTOM and rule.custom_fn:
            try:
                if rule.custom_fn(content):
                    return "custom_match"
            except Exception:
                return None
        return None

    def _redact(self, rule: GuardrailRule, content: str) -> str:
        pattern = self._compiled.get(rule.rule_id)
        if pattern:
            return pattern.sub("[REDACTED]", content)
        return content

    @classmethod
    def default(cls, audit_log: Optional[AuditLog] = None) -> "GuardrailEngine":
        """开箱即用的默认规则集。"""
        return cls(rules=[
            GuardrailRule.prompt_injection(),
            GuardrailRule.pii(),
            GuardrailRule.length("Output too long", max_chars=8000,
                                 action=RuleAction.WARN, apply_to="output"),
            GuardrailRule.keyword("Toxic words",
                                  ["kill", "die", "傻", "蠢", "白痴"],
                                  action=RuleAction.WARN, severity="medium"),
        ], audit_log=audit_log)
