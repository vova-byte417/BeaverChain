"""Workflow DSL parser - YAML/JSON workflow definition."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .core.workflow import Workflow, WorkflowNode, WorkflowEdge, NodeType
from .core.conditions import Condition, ConditionType


class DSLError(Exception):
    """DSL parsing error."""
    pass


class WorkflowDSL:
    """Parse workflow definitions from dict / JSON / YAML."""

    @classmethod
    def from_dict(cls, spec: Dict[str, Any]) -> Workflow:
        """Build a Workflow from a dict spec.

        Spec format::

            {
              "name": "my_workflow",
              "description": "...",
              "nodes": [
                {"id": "n1", "name": "Start", "type": "start"},
                {"id": "n2", "name": "Call model", "type": "model",
                 "config": {"model_name": "gpt-4"}},
                {"id": "n3", "name": "End", "type": "end"}
              ],
              "edges": [
                {"from": "n1", "to": "n2"},
                {"from": "n2", "to": "n3"}
              ],
              "entry": "n1",
              "exits": ["n3"]
            }
        """
        if "name" not in spec:
            raise DSLError("Workflow spec must include 'name'")

        wf = Workflow(name=spec["name"], description=spec.get("description", ""))

        for node_spec in spec.get("nodes", []):
            try:
                node_type = NodeType(node_spec.get("type", "model"))
            except ValueError as e:
                raise DSLError(f"Invalid node type: {node_spec.get('type')}") from e

            node = WorkflowNode(
                node_id=node_spec.get("id") or node_spec.get("node_id") or f"n_{len(wf.nodes)}",
                name=node_spec.get("name", node_spec.get("id", "node")),
                node_type=node_type,
                config=node_spec.get("config", {}),
                input_mapping=node_spec.get("input_mapping", {}),
                output_mapping=node_spec.get("output_mapping", {}),
                retry_config=node_spec.get("retry_config", {"max_retries": 3, "retry_delay": 1.0, "backoff_factor": 2.0}),
                timeout=node_spec.get("timeout", 300.0),
            )
            wf.add_node(node)

        for edge_spec in spec.get("edges", []):
            from_node = edge_spec.get("from") or edge_spec.get("from_node")
            to_node = edge_spec.get("to") or edge_spec.get("to_node")
            if not from_node or not to_node:
                raise DSLError(f"Edge must include 'from' and 'to': {edge_spec}")

            condition = None
            cond_spec = edge_spec.get("condition")
            if cond_spec:
                condition = cls._build_condition(cond_spec).to_edge_condition()

            edge = WorkflowEdge(
                from_node=from_node,
                to_node=to_node,
                condition=condition,
                condition_label=edge_spec.get("label"),
            )
            wf.add_edge(edge)

        entry = spec.get("entry") or spec.get("entry_point")
        if entry:
            wf.set_entry_point(entry)
        elif wf.nodes:
            # default to first node
            wf.set_entry_point(next(iter(wf.nodes.keys())))

        for exit_id in spec.get("exits", spec.get("exit_points", [])):
            wf.add_exit_point(exit_id)

        wf.metadata = spec.get("metadata", {})
        return wf

    @classmethod
    def _build_condition(cls, cond_spec: Dict[str, Any]) -> Condition:
        op = cond_spec.get("op") or cond_spec.get("type")
        if not op:
            raise DSLError(f"Condition must include 'op' or 'type': {cond_spec}")

        try:
            cond_type = ConditionType(op)
        except ValueError as e:
            raise DSLError(f"Invalid condition op: {op}") from e

        sub_conditions = []
        for sub in cond_spec.get("conditions", []):
            sub_conditions.append(cls._build_condition(sub))

        return Condition(
            condition_type=cond_type,
            key=cond_spec.get("key"),
            value=cond_spec.get("value"),
            sub_conditions=sub_conditions,
        )

    @classmethod
    def from_json(cls, json_str: str) -> Workflow:
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_json_file(cls, path: str) -> Workflow:
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def from_yaml(cls, yaml_str: str) -> Workflow:
        try:
            import yaml  # type: ignore
        except ImportError as e:
            raise DSLError("PyYAML is required for YAML parsing. pip install pyyaml") from e
        return cls.from_dict(yaml.safe_load(yaml_str))

    @classmethod
    def to_json(cls, workflow: Workflow, indent: int = 2) -> str:
        return json.dumps(workflow.to_dict(), indent=indent, ensure_ascii=False)


def dsl_parser(spec: Any) -> Workflow:
    """Convenience: parse from dict/JSON string/file path."""
    if isinstance(spec, dict):
        return WorkflowDSL.from_dict(spec)
    if isinstance(spec, str):
        s = spec.strip()
        if s.startswith("{") or s.startswith("["):
            return WorkflowDSL.from_json(s)
        # treat as path
        return WorkflowDSL.from_json_file(s)
    raise DSLError(f"Unsupported spec type: {type(spec).__name__}")
