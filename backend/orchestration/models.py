"""Data models for orchestration: agents, tools, snapshots."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentRole(Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    CRITIC = "critic"
    TOOL_USER = "tool_user"
    COORDINATOR = "coordinator"
    USER_PROXY = "user_proxy"


@dataclass
class Agent:
    """Agent definition for multi-agent orchestration."""
    agent_id: str
    name: str
    role: AgentRole
    model: str
    system_prompt: str = ""
    tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, name: str, role: AgentRole, model: str = "gpt-4", **kwargs) -> "Agent":
        return cls(
            agent_id=kwargs.pop("agent_id", f"agent_{uuid.uuid4().hex[:8]}"),
            name=name,
            role=role,
            model=model,
            **kwargs,
        )


@dataclass
class ToolCall:
    """Recorded tool invocation."""
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    agent_id: Optional[str] = None

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000


@dataclass
class TokenStats:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LatencyStats:
    total_ms: float = 0.0
    count: int = 0
    min_ms: float = 0.0
    max_ms: float = 0.0
    avg_ms: float = 0.0


@dataclass
class ExecutionSnapshot:
    """Snapshot of node inputs/outputs at a point in time."""
    snapshot_id: str
    node_id: str
    run_id: str
    timestamp: float = field(default_factory=time.time)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
