"""Evaluation metrics: hallucination, toxicity, faithfulness, relevance, context recall/precision.

每个 metric 都实现：
- 启发式 (heuristic) 计算：基于 token 重叠 / 词典匹配，零依赖、可单测
- LLM-as-judge 接口：传入 judge_fn 由上层注入真实模型

返回统一的 MetricResult，便于聚合和报告生成。
"""

from __future__ import annotations

import re
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Set


JudgeFn = Callable[[str, str], float]  # (prompt, response) -> score in [0,1]


@dataclass
class MetricResult:
    name: str
    score: float          # 标准化到 [0, 1]，1 = 最好（toxicity/hallucination 取反后存储）
    raw_value: float      # 原始值（如 toxicity 命中数）
    passed: bool          # 是否通过阈值
    details: Dict[str, Any] = field(default_factory=dict)
    threshold: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 4),
            "raw_value": self.raw_value,
            "passed": self.passed,
            "threshold": self.threshold,
            "details": self.details,
        }


class BaseMetric(ABC):
    name: str = "base"
    higher_is_better: bool = True

    def __init__(self, threshold: float = 0.5, judge_fn: Optional[JudgeFn] = None):
        self.threshold = threshold
        self.judge_fn = judge_fn

    @abstractmethod
    def compute(self, **kwargs) -> MetricResult:
        ...

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    @staticmethod
    def _ngrams(tokens: Sequence[str], n: int) -> Set[tuple]:
        return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


# --------------------------------- Hallucination ---------------------------------

class HallucinationMetric(BaseMetric):
    """幻觉率：response 中无法被 context 支持的 claim 占比 (越低越好)。

    启发式实现：把 response 切成句子，每句若与 context 的 token 重叠率 < 0.3 视为幻觉。
    """
    name = "hallucination"
    higher_is_better = False

    def __init__(self, threshold: float = 0.3, sentence_overlap_threshold: float = 0.3,
                 judge_fn: Optional[JudgeFn] = None):
        super().__init__(threshold=threshold, judge_fn=judge_fn)
        self.sentence_overlap_threshold = sentence_overlap_threshold

    def compute(self, response: str, context: str = "", **_) -> MetricResult:
        if self.judge_fn:
            raw = self.judge_fn(context, response)
            score = 1.0 - max(0.0, min(1.0, raw))
            return MetricResult(self.name, score, raw, raw <= self.threshold,
                                {"method": "judge"}, self.threshold)

        sentences = [s.strip() for s in re.split(r"[.!?。！？\n]", response) if s.strip()]
        if not sentences:
            return MetricResult(self.name, 1.0, 0.0, True, {"sentences": 0}, self.threshold)

        ctx_tokens = set(self._tokenize(context))
        hallucinated = 0
        per_sentence = []
        for sent in sentences:
            sent_tokens = self._tokenize(sent)
            if not sent_tokens:
                continue
            overlap = len(set(sent_tokens) & ctx_tokens) / len(sent_tokens)
            is_halluc = overlap < self.sentence_overlap_threshold and len(ctx_tokens) > 0
            if is_halluc:
                hallucinated += 1
            per_sentence.append({"text": sent[:80], "overlap": round(overlap, 3),
                                 "hallucinated": is_halluc})

        rate = hallucinated / len(sentences)
        score = 1.0 - rate
        return MetricResult(
            self.name, score, rate, rate <= self.threshold,
            {"sentences": len(sentences), "hallucinated": hallucinated,
             "per_sentence": per_sentence[:10]},
            self.threshold,
        )


# --------------------------------- Toxicity ---------------------------------

DEFAULT_TOXIC_LEXICON = {
    "hate", "hatred", "kill", "stupid", "idiot", "dumb", "racist",
    "violence", "abuse", "harm", "attack", "threat", "die",
    "fuck", "shit", "damn", "bastard",
    # 中文示例
    "傻", "蠢", "笨蛋", "去死", "白痴", "废物",
}


class ToxicityMetric(BaseMetric):
    """毒性：响应中命中毒性词典的比例 (越低越好)。

    启发式：词典匹配 + 简单模式匹配（如全大写连续辱骂）。
    生产中应替换为 Detoxify / Perspective API。
    """
    name = "toxicity"
    higher_is_better = False

    def __init__(self, threshold: float = 0.05, lexicon: Optional[Set[str]] = None,
                 judge_fn: Optional[JudgeFn] = None):
        super().__init__(threshold=threshold, judge_fn=judge_fn)
        self.lexicon = lexicon or DEFAULT_TOXIC_LEXICON

    def compute(self, response: str, **_) -> MetricResult:
        if self.judge_fn:
            raw = self.judge_fn("", response)
            score = 1.0 - max(0.0, min(1.0, raw))
            return MetricResult(self.name, score, raw, raw <= self.threshold,
                                {"method": "judge"}, self.threshold)

        tokens = self._tokenize(response)
        if not tokens:
            return MetricResult(self.name, 1.0, 0.0, True, {"hits": []}, self.threshold)

        hits = [t for t in tokens if t in self.lexicon]
        rate = len(hits) / len(tokens)
        return MetricResult(
            self.name, 1.0 - min(1.0, rate * 5),  # 放大显示
            rate, rate <= self.threshold,
            {"total_tokens": len(tokens), "hit_count": len(hits), "hits": hits[:20]},
            self.threshold,
        )


# --------------------------------- Faithfulness ---------------------------------

class FaithfulnessMetric(BaseMetric):
    """忠实度：response 中的 claim 能被 context 支持的比例 (越高越好)。

    与 Hallucination 互补：faithfulness ≈ 1 - hallucination_rate，但这里用 bigram 重叠粒度更细。
    """
    name = "faithfulness"

    def __init__(self, threshold: float = 0.7, judge_fn: Optional[JudgeFn] = None):
        super().__init__(threshold=threshold, judge_fn=judge_fn)

    def compute(self, response: str, context: str = "", **_) -> MetricResult:
        if self.judge_fn:
            raw = self.judge_fn(context, response)
            score = max(0.0, min(1.0, raw))
            return MetricResult(self.name, score, raw, score >= self.threshold,
                                {"method": "judge"}, self.threshold)

        resp_tokens = self._tokenize(response)
        ctx_tokens = self._tokenize(context)
        if not resp_tokens or not ctx_tokens:
            return MetricResult(self.name, 0.0, 0.0, False,
                                {"reason": "empty input"}, self.threshold)

        resp_bigrams = self._ngrams(resp_tokens, 2)
        ctx_bigrams = self._ngrams(ctx_tokens, 2)
        if not resp_bigrams:
            return MetricResult(self.name, 0.0, 0.0, False,
                                {"reason": "no bigrams"}, self.threshold)

        supported = len(resp_bigrams & ctx_bigrams)
        score = supported / len(resp_bigrams)
        return MetricResult(
            self.name, score, score, score >= self.threshold,
            {"resp_bigrams": len(resp_bigrams), "supported": supported},
            self.threshold,
        )


# --------------------------------- Relevance ---------------------------------

class RelevanceMetric(BaseMetric):
    """相关性：response 与 query 的语义相关度 (越高越好)。

    启发式：query token 在 response 中的覆盖率 + bigram 重叠。
    """
    name = "relevance"

    def compute(self, query: str, response: str, **_) -> MetricResult:
        if self.judge_fn:
            raw = self.judge_fn(query, response)
            score = max(0.0, min(1.0, raw))
            return MetricResult(self.name, score, raw, score >= self.threshold,
                                {"method": "judge"}, self.threshold)

        q_tokens = set(self._tokenize(query))
        r_tokens = set(self._tokenize(response))
        if not q_tokens:
            return MetricResult(self.name, 0.0, 0.0, False,
                                {"reason": "empty query"}, self.threshold)

        coverage = len(q_tokens & r_tokens) / len(q_tokens)

        q_bi = self._ngrams(self._tokenize(query), 2)
        r_bi = self._ngrams(self._tokenize(response), 2)
        bi_overlap = (len(q_bi & r_bi) / len(q_bi)) if q_bi else 0.0

        score = 0.6 * coverage + 0.4 * bi_overlap
        return MetricResult(
            self.name, score, score, score >= self.threshold,
            {"keyword_coverage": round(coverage, 3),
             "bigram_overlap": round(bi_overlap, 3)},
            self.threshold,
        )


# --------------------------------- Context Recall/Precision ---------------------------------

class ContextRecallMetric(BaseMetric):
    """Context Recall：标准答案中能被检索到的 context 覆盖的比例。"""
    name = "context_recall"

    def compute(self, ground_truth: str, contexts: Sequence[str], **_) -> MetricResult:
        gt_tokens = set(self._tokenize(ground_truth))
        if not gt_tokens:
            return MetricResult(self.name, 0.0, 0.0, False,
                                {"reason": "empty ground truth"}, self.threshold)

        all_ctx_tokens: Set[str] = set()
        for c in contexts:
            all_ctx_tokens |= set(self._tokenize(c))

        recalled = len(gt_tokens & all_ctx_tokens)
        score = recalled / len(gt_tokens)
        return MetricResult(
            self.name, score, score, score >= self.threshold,
            {"gt_tokens": len(gt_tokens), "recalled": recalled,
             "context_count": len(contexts)},
            self.threshold,
        )


class ContextPrecisionMetric(BaseMetric):
    """Context Precision：检索到的 context 中真正相关（与 ground truth 重叠）的比例。"""
    name = "context_precision"

    def compute(self, ground_truth: str, contexts: Sequence[str], **_) -> MetricResult:
        gt_tokens = set(self._tokenize(ground_truth))
        if not contexts or not gt_tokens:
            return MetricResult(self.name, 0.0, 0.0, False,
                                {"reason": "empty input"}, self.threshold)

        per_ctx_score = []
        relevant_count = 0
        for i, c in enumerate(contexts):
            c_tokens = set(self._tokenize(c))
            overlap = (len(gt_tokens & c_tokens) / len(c_tokens)) if c_tokens else 0
            relevant = overlap >= 0.1
            if relevant:
                relevant_count += 1
            per_ctx_score.append({"index": i, "overlap": round(overlap, 3),
                                  "relevant": relevant})

        score = relevant_count / len(contexts)
        return MetricResult(
            self.name, score, score, score >= self.threshold,
            {"context_count": len(contexts), "relevant": relevant_count,
             "per_context": per_ctx_score},
            self.threshold,
        )


# --------------------------------- Suite ---------------------------------

class MetricSuite:
    """组合多个 metric，一次性评估并聚合。"""

    def __init__(self, metrics: Optional[List[BaseMetric]] = None):
        self.metrics: List[BaseMetric] = metrics or [
            HallucinationMetric(),
            ToxicityMetric(),
            FaithfulnessMetric(),
            RelevanceMetric(),
            ContextRecallMetric(),
            ContextPrecisionMetric(),
        ]

    def evaluate(self, *, query: str = "", response: str = "",
                 context: str = "", contexts: Optional[Sequence[str]] = None,
                 ground_truth: str = "") -> Dict[str, MetricResult]:
        if contexts is None:
            contexts = [context] if context else []
        joined_context = context or "\n".join(contexts)

        results: Dict[str, MetricResult] = {}
        for m in self.metrics:
            try:
                if m.name in ("context_recall", "context_precision"):
                    res = m.compute(ground_truth=ground_truth, contexts=contexts)
                elif m.name in ("hallucination", "faithfulness"):
                    res = m.compute(response=response, context=joined_context)
                elif m.name == "toxicity":
                    res = m.compute(response=response)
                elif m.name == "relevance":
                    res = m.compute(query=query, response=response)
                else:
                    res = m.compute(query=query, response=response,
                                    context=joined_context, contexts=contexts,
                                    ground_truth=ground_truth)
                results[m.name] = res
            except Exception as e:
                results[m.name] = MetricResult(
                    m.name, 0.0, 0.0, False, {"error": str(e)}, m.threshold
                )
        return results

    def aggregate_score(self, results: Dict[str, MetricResult]) -> float:
        if not results:
            return 0.0
        return sum(r.score for r in results.values()) / len(results)

    def all_passed(self, results: Dict[str, MetricResult]) -> bool:
        return all(r.passed for r in results.values())
