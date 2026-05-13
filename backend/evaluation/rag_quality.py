"""RAG 质量监控：检索质量评估 + 上下文利用率统计."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .metrics import (
    ContextRecallMetric,
    ContextPrecisionMetric,
    FaithfulnessMetric,
    RelevanceMetric,
    MetricResult,
)


def _tokens(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


@dataclass
class RetrievalEvalResult:
    """单次检索的评估结果。"""
    query: str
    retrieved_count: int
    relevant_count: int
    precision: float
    recall: float
    f1: float
    mrr: float          # Mean Reciprocal Rank
    ndcg_at_k: float    # nDCG@k
    hit_rate: float     # 是否命中至少一个相关文档
    per_context_relevance: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "retrieved_count": self.retrieved_count,
            "relevant_count": self.relevant_count,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "mrr": round(self.mrr, 4),
            "ndcg_at_k": round(self.ndcg_at_k, 4),
            "hit_rate": self.hit_rate,
            "per_context_relevance": self.per_context_relevance,
        }


@dataclass
class ContextUtilization:
    """上下文利用率：response 中实际引用的 context 占比。"""
    total_contexts: int
    used_contexts: int
    utilization_rate: float
    per_context_usage: List[Dict[str, Any]] = field(default_factory=list)
    unused_context_indices: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_contexts": self.total_contexts,
            "used_contexts": self.used_contexts,
            "utilization_rate": round(self.utilization_rate, 4),
            "per_context_usage": self.per_context_usage,
            "unused_context_indices": self.unused_context_indices,
        }


class RAGQualityMonitor:
    """RAG 质量综合监控器."""

    def __init__(self,
                 relevance_threshold: float = 0.1,
                 ndcg_k: int = 5,
                 utilization_threshold: float = 0.05):
        self.relevance_threshold = relevance_threshold
        self.ndcg_k = ndcg_k
        self.utilization_threshold = utilization_threshold
        self._faith = FaithfulnessMetric()
        self._relev = RelevanceMetric()
        self._ctx_recall = ContextRecallMetric()
        self._ctx_precision = ContextPrecisionMetric()

    # ----------------- 检索质量 -----------------

    def evaluate_retrieval(self, query: str, contexts: Sequence[str],
                            ground_truth: str = "",
                            relevant_doc_ids: Optional[List[int]] = None
                            ) -> RetrievalEvalResult:
        """评估检索质量。

        relevant_doc_ids: 已知的相关文档下标列表（可选）。
        若不提供，使用 ground_truth token 重叠率自动判定。
        """
        n = len(contexts)
        if n == 0:
            return RetrievalEvalResult(query, 0, 0, 0, 0, 0, 0, 0, 0, [])

        # 1) 判定每个文档是否相关
        per_ctx: List[Dict[str, Any]] = []
        relevance_flags: List[bool] = []

        if relevant_doc_ids is not None:
            for i, ctx in enumerate(contexts):
                rel = i in relevant_doc_ids
                relevance_flags.append(rel)
                per_ctx.append({"index": i, "relevant": rel,
                                "method": "ground_truth_id"})
        else:
            gt_tokens = set(_tokens(ground_truth)) if ground_truth else set(_tokens(query))
            for i, ctx in enumerate(contexts):
                ctx_tokens = set(_tokens(ctx))
                if not ctx_tokens or not gt_tokens:
                    overlap = 0.0
                else:
                    overlap = len(gt_tokens & ctx_tokens) / len(gt_tokens)
                rel = overlap >= self.relevance_threshold
                relevance_flags.append(rel)
                per_ctx.append({"index": i, "overlap": round(overlap, 3),
                                "relevant": rel, "method": "token_overlap"})

        relevant_count = sum(relevance_flags)

        # 2) precision / recall / f1
        precision = relevant_count / n
        # recall：若有 relevant_doc_ids 用其总数，否则按 ground_truth 命中比例
        if relevant_doc_ids:
            total_relevant = max(len(relevant_doc_ids), 1)
            recall = relevant_count / total_relevant
        else:
            # 简化：假设召回率 = 相关数 / 期望召回数 (取 min(retrieved, 5))
            expected = min(n, 5)
            recall = relevant_count / expected if expected else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        # 3) MRR
        mrr = 0.0
        for i, rel in enumerate(relevance_flags):
            if rel:
                mrr = 1.0 / (i + 1)
                break

        # 4) nDCG@k
        ndcg = self._ndcg(relevance_flags[:self.ndcg_k], k=self.ndcg_k)

        # 5) hit_rate
        hit = 1.0 if relevant_count > 0 else 0.0

        return RetrievalEvalResult(
            query=query,
            retrieved_count=n,
            relevant_count=relevant_count,
            precision=precision,
            recall=recall,
            f1=f1,
            mrr=mrr,
            ndcg_at_k=ndcg,
            hit_rate=hit,
            per_context_relevance=per_ctx,
        )

    @staticmethod
    def _ndcg(rel_flags: Sequence[bool], k: int) -> float:
        import math
        if not rel_flags:
            return 0.0
        # DCG
        dcg = sum((1.0 if r else 0.0) / math.log2(i + 2)
                  for i, r in enumerate(rel_flags))
        # 理想排序
        ideal = sorted(rel_flags, reverse=True)
        idcg = sum((1.0 if r else 0.0) / math.log2(i + 2)
                   for i, r in enumerate(ideal))
        return (dcg / idcg) if idcg > 0 else 0.0

    # ----------------- 上下文利用率 -----------------

    def evaluate_context_utilization(self, response: str,
                                       contexts: Sequence[str]) -> ContextUtilization:
        """评估 response 实际利用了多少 context。

        启发式：每个 context 与 response 的 unigram 重叠率超过阈值则视为被使用。
        """
        n = len(contexts)
        if n == 0:
            return ContextUtilization(0, 0, 0.0, [], [])

        resp_tokens = set(_tokens(response))
        used = 0
        per_usage: List[Dict[str, Any]] = []
        unused: List[int] = []

        for i, ctx in enumerate(contexts):
            ctx_tokens = set(_tokens(ctx))
            if not ctx_tokens:
                per_usage.append({"index": i, "overlap": 0.0, "used": False})
                unused.append(i)
                continue
            overlap = len(resp_tokens & ctx_tokens) / len(ctx_tokens)
            is_used = overlap >= self.utilization_threshold
            if is_used:
                used += 1
            else:
                unused.append(i)
            per_usage.append({"index": i, "overlap": round(overlap, 3),
                              "used": is_used,
                              "context_preview": ctx[:80]})

        return ContextUtilization(
            total_contexts=n,
            used_contexts=used,
            utilization_rate=used / n,
            per_context_usage=per_usage,
            unused_context_indices=unused,
        )

    # ----------------- 综合评估 -----------------

    def full_evaluate(self, query: str, response: str, contexts: Sequence[str],
                       ground_truth: str = "",
                       relevant_doc_ids: Optional[List[int]] = None
                       ) -> Dict[str, Any]:
        """一站式 RAG 评估：检索 + 利用率 + 忠实度 + 相关性 + recall/precision."""
        joined_ctx = "\n".join(contexts)

        retrieval = self.evaluate_retrieval(query, contexts, ground_truth,
                                              relevant_doc_ids)
        utilization = self.evaluate_context_utilization(response, contexts)

        faith: MetricResult = self._faith.compute(response=response, context=joined_ctx)
        relev: MetricResult = self._relev.compute(query=query, response=response)

        ctx_recall = self._ctx_recall.compute(ground_truth=ground_truth or query,
                                                contexts=contexts)
        ctx_precision = self._ctx_precision.compute(ground_truth=ground_truth or query,
                                                      contexts=contexts)

        # 综合分：加权平均
        composite = (
            0.25 * retrieval.f1
            + 0.15 * retrieval.mrr
            + 0.15 * retrieval.ndcg_at_k
            + 0.20 * faith.score
            + 0.10 * relev.score
            + 0.15 * utilization.utilization_rate
        )

        return {
            "query": query,
            "composite_score": round(composite, 4),
            "retrieval": retrieval.to_dict(),
            "context_utilization": utilization.to_dict(),
            "faithfulness": faith.to_dict(),
            "relevance": relev.to_dict(),
            "context_recall": ctx_recall.to_dict(),
            "context_precision": ctx_precision.to_dict(),
        }
