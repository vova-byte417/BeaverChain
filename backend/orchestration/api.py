"""FastAPI routes for orchestration & lineage visualization."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException, Query
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    APIRouter = None  # type: ignore
    BaseModel = object  # type: ignore

from .core.executor import WorkflowExecutor
from .dsl import WorkflowDSL, DSLError
from .lineage.storage import LineageStorage, InMemoryStorage
from .lineage.tracker import LineageTracker
from .lineage.query import LineageQuery, QueryOperator
from .visualization import Visualizer, GraphFormat, TimelineVisualizer


_TRACKER = LineageTracker()
_STORAGE: LineageStorage = InMemoryStorage()


def get_tracker() -> LineageTracker:
    return _TRACKER


def get_storage() -> LineageStorage:
    return _STORAGE


def set_storage(storage: LineageStorage) -> None:
    global _STORAGE
    _STORAGE = storage


if HAS_FASTAPI:

    router = APIRouter(prefix="/orchestration", tags=["orchestration"])

    class WorkflowRunRequest(BaseModel):
        spec: Dict[str, Any]
        initial_context: Optional[Dict[str, Any]] = None

    @router.post("/workflows/run")
    async def run_workflow(req: WorkflowRunRequest):
        try:
            workflow = WorkflowDSL.from_dict(req.spec)
        except DSLError as e:
            raise HTTPException(status_code=400, detail=str(e))

        executor = WorkflowExecutor(workflow, lineage_tracker=_TRACKER)
        try:
            result = await executor.execute(req.initial_context or {})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Execution failed: {e}")

        record = _TRACKER.get_record(result.run_id)
        if record:
            _STORAGE.save(record)

        return {
            "run_id": result.run_id,
            "workflow_id": result.workflow_id,
            "status": result.status.value,
            "duration_ms": result.duration * 1000,
            "success_count": result.success_count,
            "failed_count": result.failed_count,
        }

    @router.post("/workflows/validate")
    def validate_workflow(spec: Dict[str, Any]):
        try:
            workflow = WorkflowDSL.from_dict(spec)
        except DSLError as e:
            raise HTTPException(status_code=400, detail=str(e))
        errors = workflow.validate()
        return {"valid": len(errors) == 0, "errors": errors}

    @router.get("/workflows/render")
    def render_workflow(spec: Dict[str, Any], format: str = Query("mermaid")):
        try:
            workflow = WorkflowDSL.from_dict(spec)
            fmt = GraphFormat(format)
        except (DSLError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"format": format, "content": Visualizer.render(workflow, fmt)}

    @router.get("/lineage/{run_id}")
    def get_lineage(run_id: str):
        record = _TRACKER.get_record(run_id) or _STORAGE.load(run_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
        return record.to_dict()

    @router.get("/lineage/{run_id}/graph")
    def get_lineage_graph(run_id: str, format: str = Query("mermaid")):
        record = _TRACKER.get_record(run_id) or _STORAGE.load(run_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
        try:
            fmt = GraphFormat(format)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"format": format, "content": Visualizer.render(record, fmt)}

    @router.get("/lineage/{run_id}/timeline")
    def get_timeline(run_id: str, format: str = Query("text")):
        record = _TRACKER.get_record(run_id) or _STORAGE.load(run_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
        if format == "gantt":
            return {"format": "gantt", "content": TimelineVisualizer.to_mermaid_gantt(record)}
        return {"format": "text", "content": TimelineVisualizer.to_text_timeline(record)}

    @router.get("/lineage")
    def list_lineage(
        limit: int = Query(20, ge=1, le=200),
        offset: int = Query(0, ge=0),
        workflow_name: Optional[str] = None,
        success: Optional[bool] = None,
        last_hours: Optional[int] = None,
    ):
        query = LineageQuery(_STORAGE)
        if workflow_name:
            query = query.filter_workflow_name(workflow_name)
        if success is not None:
            query = query.filter_success(success)
        if last_hours:
            query = query.filter_last(last_hours)
        records = query.sort_by("start_time", descending=True).offset(offset).limit(limit).execute()
        return {
            "total": _STORAGE.count(),
            "records": [
                {
                    "run_id": r.run_id,
                    "workflow_name": r.workflow_name,
                    "duration_ms": r.duration_ms,
                    "success": r.success,
                    "start_time": r.start_time,
                    "node_count": r.node_count,
                    "total_tokens": r.total_tokens.total_tokens,
                }
                for r in records
            ],
        }

    @router.get("/lineage/stats/aggregate")
    def aggregate_stats(last_hours: Optional[int] = None):
        query = LineageQuery(_STORAGE)
        if last_hours:
            query = query.filter_last(last_hours)
        return query.aggregate()

else:
    router = None
