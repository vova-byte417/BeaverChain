"""Visualization for workflows and lineage records."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from .core.workflow import Workflow
from .lineage.tracker import LineageRecord, LineageGraph


class GraphFormat(Enum):
    MERMAID = "mermaid"
    GRAPHVIZ = "graphviz"
    JSON = "json"


class Visualizer:
    """Visualize workflows and lineage records."""

    @staticmethod
    def workflow_to_mermaid(workflow: Workflow) -> str:
        """Render a workflow as a Mermaid graph."""
        type_shape = {
            "start": ("([", "])"),
            "end": ("([", "])"),
            "condition": ("{", "}"),
            "parallel": ("[/", "/]"),
            "loop": ("[(", ")]"),
        }
        lines = ["graph TD"]
        for node_id, node in workflow.nodes.items():
            open_b, close_b = type_shape.get(node.node_type.value, ("[", "]"))
            label = f"{node.name}<br/>({node.node_type.value})"
            lines.append(f"    {node_id}{open_b}\"{label}\"{close_b}")
        for edge in workflow.edges:
            label = f"|{edge.condition_label}|" if edge.condition_label else ""
            lines.append(f"    {edge.from_node} -->{label} {edge.to_node}")
        if workflow.entry_point:
            lines.append(f"    style {workflow.entry_point} fill:#90EE90")
        for exit_node in workflow.exit_points:
            lines.append(f"    style {exit_node} fill:#FFB6C1")
        return "\n".join(lines)

    @staticmethod
    def workflow_to_graphviz(workflow: Workflow) -> str:
        """Render a workflow as Graphviz DOT."""
        lines = [f'digraph "{workflow.name}" {{', "    rankdir=TB;", "    node [shape=box];"]
        for node_id, node in workflow.nodes.items():
            shape = {
                "condition": "diamond",
                "parallel": "parallelogram",
                "start": "ellipse",
                "end": "ellipse",
            }.get(node.node_type.value, "box")
            lines.append(f'    "{node_id}" [label="{node.name}\\n({node.node_type.value})", shape={shape}];')
        for edge in workflow.edges:
            label = f' [label="{edge.condition_label}"]' if edge.condition_label else ""
            lines.append(f'    "{edge.from_node}" -> "{edge.to_node}"{label};')
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def lineage_to_mermaid(record: LineageRecord) -> str:
        """Render a lineage record as a Mermaid graph."""
        return LineageGraph(record).to_mermaid()

    @classmethod
    def render(cls, target: Any, fmt: GraphFormat = GraphFormat.MERMAID) -> str:
        if isinstance(target, Workflow):
            if fmt == GraphFormat.MERMAID:
                return cls.workflow_to_mermaid(target)
            if fmt == GraphFormat.GRAPHVIZ:
                return cls.workflow_to_graphviz(target)
            if fmt == GraphFormat.JSON:
                import json
                return json.dumps(target.to_dict(), indent=2, ensure_ascii=False)
        if isinstance(target, LineageRecord):
            if fmt == GraphFormat.MERMAID:
                return cls.lineage_to_mermaid(target)
            if fmt == GraphFormat.JSON:
                import json
                return json.dumps(target.to_dict(), indent=2, ensure_ascii=False)
        raise ValueError(f"Unsupported target/format: {type(target).__name__} / {fmt}")


class TimelineVisualizer:
    """Generate execution timelines from a lineage record."""

    @staticmethod
    def to_mermaid_gantt(record: LineageRecord) -> str:
        lines = [
            "gantt",
            f"    title Execution Timeline: {record.workflow_name}",
            "    dateFormat x",
            "    axisFormat %S.%L",
        ]
        sections: Dict[str, List[Any]] = {}
        for span in record.spans.values():
            sections.setdefault(span.span_type, []).append(span)
        for section_name, spans in sections.items():
            lines.append(f"    section {section_name}")
            for span in spans:
                start_ms = int((span.start_time - record.start_time) * 1000)
                duration_ms = int(span.duration_ms)
                status = "done" if span.status == "completed" else ("crit" if span.status == "failed" else "active")
                lines.append(f"    {span.name} :{status}, {start_ms}, {duration_ms}ms")
        return "\n".join(lines)

    @staticmethod
    def to_text_timeline(record: LineageRecord) -> str:
        lines = [
            f"Timeline: {record.workflow_name} (run_id={record.run_id})",
            f"Total duration: {record.duration_ms:.1f}ms",
            "-" * 80,
        ]
        sorted_spans = sorted(record.spans.values(), key=lambda s: s.start_time)
        for span in sorted_spans:
            offset = (span.start_time - record.start_time) * 1000
            depth = TimelineVisualizer._depth(span.span_id, record)
            indent = "  " * depth
            status_char = "✓" if span.status == "completed" else ("✗" if span.status == "failed" else "•")
            lines.append(
                f"{indent}{status_char} [{offset:>8.1f}ms +{span.duration_ms:>8.1f}ms] "
                f"{span.span_type:>8} | {span.name}"
            )
        return "\n".join(lines)

    @staticmethod
    def _depth(span_id: str, record: LineageRecord) -> int:
        depth = 0
        current = record.spans.get(span_id)
        while current and current.parent_span_id:
            depth += 1
            current = record.spans.get(current.parent_span_id)
            if depth > 50:
                break
        return depth
