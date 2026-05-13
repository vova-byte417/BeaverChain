"""Example workflows demonstrating the orchestration engine."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from .core.workflow import Workflow, WorkflowNode, WorkflowEdge, NodeType
from .core.executor import WorkflowExecutor
from .core.conditions import Condition
from .dsl import WorkflowDSL
from .lineage.tracker import LineageTracker
from .visualization import Visualizer, GraphFormat, TimelineVisualizer


# ------------------------------ Example 1: Simple linear pipeline ------------------------------

def build_simple_qa_workflow() -> Workflow:
    """Linear flow: input -> retrieve -> generate -> output."""
    wf = Workflow(name="simple_qa", description="Simple QA pipeline")

    n_input = WorkflowNode.create("Input", NodeType.START, node_id="input")
    n_retrieve = WorkflowNode.create("Retrieve context", NodeType.TOOL, node_id="retrieve",
                                     config={"tool_name": "vector_search"})
    n_generate = WorkflowNode.create("Generate answer", NodeType.MODEL, node_id="generate",
                                     config={"model_name": "gpt-4"})
    n_output = WorkflowNode.create("Output", NodeType.END, node_id="output")

    wf.add_nodes([n_input, n_retrieve, n_generate, n_output])
    wf.add_edges([
        WorkflowEdge.create("input", "retrieve"),
        WorkflowEdge.create("retrieve", "generate"),
        WorkflowEdge.create("generate", "output"),
    ])
    wf.set_entry_point("input").add_exit_point("output")
    return wf


# ------------------------------ Example 2: Conditional branch ------------------------------

def build_router_workflow() -> Workflow:
    """Router: classify intent, then route to specialized agents."""
    wf = Workflow(name="intent_router", description="Route to specialized agents based on intent")

    nodes = [
        WorkflowNode.create("Classify intent", NodeType.MODEL, node_id="classifier",
                            config={"model_name": "gpt-4"}),
        WorkflowNode.create("Code agent", NodeType.AGENT, node_id="code_agent",
                            config={"role": "code_specialist"}),
        WorkflowNode.create("Search agent", NodeType.AGENT, node_id="search_agent",
                            config={"role": "search_specialist"}),
        WorkflowNode.create("Aggregate", NodeType.AGGREGATE, node_id="aggregate"),
    ]
    wf.add_nodes(nodes)

    wf.add_edge(WorkflowEdge.create(
        "classifier", "code_agent",
        condition=Condition.equals("intent", "code").to_edge_condition(),
        condition_label="intent=code",
    ))
    wf.add_edge(WorkflowEdge.create(
        "classifier", "search_agent",
        condition=Condition.equals("intent", "search").to_edge_condition(),
        condition_label="intent=search",
    ))
    wf.connect("code_agent", "aggregate")
    wf.connect("search_agent", "aggregate")
    wf.set_entry_point("classifier").add_exit_point("aggregate")
    return wf


# ------------------------------ Example 3: Multi-agent collaboration ------------------------------

def build_multi_agent_workflow() -> Workflow:
    """Planner -> parallel executors -> reviewer."""
    wf = Workflow(name="multi_agent", description="Planner + parallel executors + reviewer")

    nodes = [
        WorkflowNode.create("Planner", NodeType.AGENT, node_id="planner",
                            config={"role": "planner", "model": "gpt-4"}),
        WorkflowNode.create("Executor A", NodeType.AGENT, node_id="exec_a",
                            config={"role": "executor", "model": "gpt-3.5-turbo"}),
        WorkflowNode.create("Executor B", NodeType.AGENT, node_id="exec_b",
                            config={"role": "executor", "model": "gpt-3.5-turbo"}),
        WorkflowNode.create("Executor C", NodeType.AGENT, node_id="exec_c",
                            config={"role": "executor", "model": "gpt-3.5-turbo"}),
        WorkflowNode.create("Reviewer", NodeType.AGENT, node_id="reviewer",
                            config={"role": "reviewer", "model": "gpt-4"}),
    ]
    wf.add_nodes(nodes)
    wf.add_edges([
        WorkflowEdge.create("planner", "exec_a"),
        WorkflowEdge.create("planner", "exec_b"),
        WorkflowEdge.create("planner", "exec_c"),
        WorkflowEdge.create("exec_a", "reviewer"),
        WorkflowEdge.create("exec_b", "reviewer"),
        WorkflowEdge.create("exec_c", "reviewer"),
    ])
    wf.set_entry_point("planner").add_exit_point("reviewer")
    return wf


# ------------------------------ Example 4: DSL-defined workflow ------------------------------

DSL_EXAMPLE = {
    "name": "rag_pipeline",
    "description": "RAG pipeline defined via DSL",
    "nodes": [
        {"id": "embed", "name": "Embed query", "type": "tool",
         "config": {"tool_name": "embedding"}},
        {"id": "retrieve", "name": "Vector search", "type": "tool",
         "config": {"tool_name": "vector_search", "top_k": 5}},
        {"id": "rerank", "name": "Rerank", "type": "model",
         "config": {"model_name": "rerank-v2"}},
        {"id": "generate", "name": "Generate answer", "type": "model",
         "config": {"model_name": "gpt-4"}},
    ],
    "edges": [
        {"from": "embed", "to": "retrieve"},
        {"from": "retrieve", "to": "rerank"},
        {"from": "rerank", "to": "generate"},
    ],
    "entry": "embed",
    "exits": ["generate"],
}


# ------------------------------ Run examples ------------------------------

async def run_example(workflow: Workflow, initial_context: Dict[str, Any]) -> None:
    tracker = LineageTracker()
    executor = WorkflowExecutor(workflow, lineage_tracker=tracker)
    result = await executor.execute(initial_context)

    print(f"\n=== Workflow: {workflow.name} ===")
    print(f"Status: {result.status.value}, duration: {result.duration*1000:.1f}ms")
    print(f"Success: {result.success_count}, Failed: {result.failed_count}")

    record = tracker.get_record(result.run_id)
    if record:
        print("\n--- Timeline ---")
        print(TimelineVisualizer.to_text_timeline(record))
        print("\n--- Lineage Graph (Mermaid) ---")
        print(Visualizer.render(record, GraphFormat.MERMAID))


async def main() -> None:
    # Example 1: simple QA
    await run_example(build_simple_qa_workflow(), {"query": "What is RAG?"})

    # Example 2: router
    await run_example(build_router_workflow(), {"intent": "code", "task": "Write a sort function"})

    # Example 3: multi-agent
    await run_example(build_multi_agent_workflow(), {"goal": "Build a CRUD API"})

    # Example 4: DSL
    wf = WorkflowDSL.from_dict(DSL_EXAMPLE)
    await run_example(wf, {"query": "Explain the architecture"})


if __name__ == "__main__":
    asyncio.run(main())
