"""
Lineage 存储模块
Lineage Storage Module
"""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from pathlib import Path

from .tracker import LineageRecord


class LineageStorage(ABC):
    """Lineage 存储抽象基类"""
    
    @abstractmethod
    def save(self, record: LineageRecord) -> None:
        """保存记录"""
        pass
    
    @abstractmethod
    def load(self, run_id: str) -> Optional[LineageRecord]:
        """加载记录"""
        pass
    
    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> List[LineageRecord]:
        """列出记录"""
        pass
    
    @abstractmethod
    def delete(self, run_id: str) -> bool:
        """删除记录"""
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 100) -> List[LineageRecord]:
        """搜索记录"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """获取记录总数"""
        pass


class InMemoryStorage(LineageStorage):
    """内存存储"""
    
    def __init__(self, max_records: int = 1000):
        self._records: Dict[str, LineageRecord] = {}
        self._max_records = max_records
    
    def save(self, record: LineageRecord) -> None:
        """保存记录"""
        # 如果超过最大数量，删除最旧的
        if len(self._records) >= self._max_records:
            oldest = min(self._records.values(), key=lambda r: r.start_time)
            del self._records[oldest.run_id]
        
        self._records[record.run_id] = record
    
    def load(self, run_id: str) -> Optional[LineageRecord]:
        """加载记录"""
        return self._records.get(run_id)
    
    def list(self, limit: int = 100, offset: int = 0) -> List[LineageRecord]:
        """列出记录"""
        records = sorted(
            self._records.values(),
            key=lambda r: r.start_time,
            reverse=True,
        )
        return records[offset:offset + limit]
    
    def delete(self, run_id: str) -> bool:
        """删除记录"""
        if run_id in self._records:
            del self._records[run_id]
            return True
        return False
    
    def search(self, query: str, limit: int = 100) -> List[LineageRecord]:
        """搜索记录"""
        query_lower = query.lower()
        results: List[LineageRecord] = []
        
        for record in self._records.values():
            # 搜索工作流名称
            if query_lower in record.workflow_name.lower():
                results.append(record)
                continue
            
            # 搜索 Span 名称
            for span in record.spans.values():
                if query_lower in span.name.lower():
                    results.append(record)
                    break
            
            if len(results) >= limit:
                break
        
        return sorted(results, key=lambda r: r.start_time, reverse=True)[:limit]
    
    def count(self) -> int:
        """获取记录总数"""
        return len(self._records)


class FileStorage(LineageStorage):
    """文件存储"""
    
    def __init__(self, storage_dir: str = "./lineage_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.storage_dir / "_index.json"
        self._index: Dict[str, Dict[str, Any]] = {}
        self._load_index()
    
    def _load_index(self) -> None:
        """加载索引"""
        if self._index_file.exists():
            with open(self._index_file, "r", encoding="utf-8") as f:
                self._index = json.load(f)
    
    def _save_index(self) -> None:
        """保存索引"""
        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2)
    
    def _get_record_path(self, run_id: str) -> Path:
        """获取记录文件路径"""
        return self.storage_dir / f"{run_id}.json"
    
    def save(self, record: LineageRecord) -> None:
        """保存记录"""
        # 保存记录文件
        filepath = self._get_record_path(record.run_id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)
        
        # 更新索引
        self._index[record.run_id] = {
            "run_id": record.run_id,
            "workflow_name": record.workflow_name,
            "workflow_id": record.workflow_id,
            "start_time": record.start_time,
            "end_time": record.end_time,
            "duration_ms": record.duration_ms,
            "success": record.success,
            "total_tokens": asdict(record.total_tokens),
            "node_count": record.node_count,
            "tool_call_count": record.tool_call_count,
        }
        self._save_index()
    
    def load(self, run_id: str) -> Optional[LineageRecord]:
        """加载记录"""
        filepath = self._get_record_path(run_id)
        if not filepath.exists():
            return None
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 重建记录
        from .tracker import Span, TokenStats
        
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
        
        return record
    
    def list(self, limit: int = 100, offset: int = 0) -> List[LineageRecord]:
        """列出记录"""
        # 按时间排序
        sorted_run_ids = sorted(
            self._index.keys(),
            key=lambda rid: self._index[rid]["start_time"],
            reverse=True,
        )
        
        result = []
        for run_id in sorted_run_ids[offset:offset + limit]:
            record = self.load(run_id)
            if record:
                result.append(record)
        
        return result
    
    def delete(self, run_id: str) -> bool:
        """删除记录"""
        filepath = self._get_record_path(run_id)
        if filepath.exists():
            filepath.unlink()
            if run_id in self._index:
                del self._index[run_id]
                self._save_index()
            return True
        return False
    
    def search(self, query: str, limit: int = 100) -> List[LineageRecord]:
        """搜索记录"""
        query_lower = query.lower()
        results: List[LineageRecord] = []
        
        # 先从索引中搜索
        for run_id, info in self._index.items():
            if query_lower in info["workflow_name"].lower():
                record = self.load(run_id)
                if record:
                    results.append(record)
            
            if len(results) >= limit:
                break
        
        # 如果结果不够，搜索 Span 名称
        if len(results) < limit:
            for run_id in self._index:
                if run_id in [r.run_id for r in results]:
                    continue
                
                record = self.load(run_id)
                if record:
                    for span in record.spans.values():
                        if query_lower in span.name.lower():
                            results.append(record)
                            break
                
                if len(results) >= limit:
                    break
        
        return sorted(results, key=lambda r: r.start_time, reverse=True)[:limit]
    
    def count(self) -> int:
        """获取记录总数"""
        return len(self._index)
    
    def cleanup_old(self, max_age_days: int = 30) -> int:
        """清理旧记录"""
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0
        
        for run_id, info in list(self._index.items()):
            if info["start_time"] < cutoff_time:
                self.delete(run_id)
                deleted_count += 1
        
        return deleted_count


class HybridStorage(LineageStorage):
    """混合存储 - 内存 + 文件"""
    
    def __init__(self, storage_dir: str = "./lineage_data", cache_size: int = 100):
        self._memory = InMemoryStorage(max_records=cache_size)
        self._file = FileStorage(storage_dir)
    
    def save(self, record: LineageRecord) -> None:
        """保存记录"""
        self._file.save(record)
        self._memory.save(record)
    
    def load(self, run_id: str) -> Optional[LineageRecord]:
        """加载记录"""
        # 先从内存加载
        record = self._memory.load(run_id)
        if record:
            return record
        
        # 从文件加载
        record = self._file.load(run_id)
        if record:
            self._memory.save(record)
        
        return record
    
    def list(self, limit: int = 100, offset: int = 0) -> List[LineageRecord]:
        """列出记录"""
        return self._file.list(limit, offset)
    
    def delete(self, run_id: str) -> bool:
        """删除记录"""
        self._memory.delete(run_id)
        return self._file.delete(run_id)
    
    def search(self, query: str, limit: int = 100) -> List[LineageRecord]:
        """搜索记录"""
        return self._file.search(query, limit)
    
    def count(self) -> int:
        """获取记录总数"""
        return self._file.count()
