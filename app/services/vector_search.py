"""Shared vector-search pipeline construction and lightweight measurements."""

from __future__ import annotations

import logging
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from statistics import fmean, median
from threading import Lock
from time import perf_counter
from typing import Any, Iterable

from app.core.config import settings

logger = logging.getLogger(__name__)


def calculate_num_candidates(limit: int) -> int:
    """Scale ANN candidates with result size while keeping MongoDB constraints valid."""
    if limit <= 0:
        raise ValueError("Vector search limit must be positive.")
    multiplier = max(1, settings.VECTOR_SEARCH_CANDIDATE_MULTIPLIER)
    minimum = max(1, settings.VECTOR_SEARCH_MIN_CANDIDATES)
    maximum = max(minimum, settings.VECTOR_SEARCH_MAX_CANDIDATES)
    scaled = max(minimum, limit * multiplier)
    # numCandidates must never be lower than limit, even above the configured cap.
    return max(limit, min(scaled, maximum))


def build_vector_search_stage(
    *, index: str, query_vector: list[float], limit: int, path: str = "embedding"
) -> dict[str, Any]:
    """Build the canonical vector stage used by all CineMate similarity queries."""
    return {
        "$vectorSearch": {
            "index": index,
            "path": path,
            "queryVector": query_vector,
            "numCandidates": calculate_num_candidates(limit),
            "limit": limit,
        }
    }


@dataclass(frozen=True)
class SearchSample:
    duration_ms: float
    scores: tuple[float, ...]


class VectorSearchMetrics:
    """Bounded in-process metrics for query latency and score distribution."""

    def __init__(self, window_size: int = 100) -> None:
        self.window_size = max(1, window_size)
        self._samples: dict[str, deque[SearchSample]] = defaultdict(
            lambda: deque(maxlen=self.window_size)
        )
        self._lock = Lock()

    def record(
        self,
        operation: str,
        duration_seconds: float,
        documents: Iterable[dict[str, Any]],
        score_field: str,
    ) -> None:
        scores = tuple(
            float(score)
            for document in documents
            if isinstance((score := document.get(score_field)), (int, float))
            and math.isfinite(float(score))
        )
        sample = SearchSample(max(0.0, duration_seconds) * 1000, scores)
        with self._lock:
            self._samples[operation].append(sample)
        logger.info(
            "vector_search operation=%s duration_ms=%.2f results=%d score_min=%s "
            "score_max=%s score_mean=%s",
            operation,
            sample.duration_ms,
            len(scores),
            f"{min(scores):.4f}" if scores else "n/a",
            f"{max(scores):.4f}" if scores else "n/a",
            f"{fmean(scores):.4f}" if scores else "n/a",
        )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            copied = {name: list(samples) for name, samples in self._samples.items()}
        return {
            "window_size": self.window_size,
            "operations": {
                name: self._summarize(samples) for name, samples in copied.items()
            },
        }

    @staticmethod
    def _summarize(samples: list[SearchSample]) -> dict[str, Any]:
        durations = [sample.duration_ms for sample in samples]
        scores = [score for sample in samples for score in sample.scores]
        sorted_durations = sorted(durations)
        p95_index = max(0, math.ceil(len(sorted_durations) * 0.95) - 1)
        return {
            "query_count": len(samples),
            "latency_ms": {
                "last": round(durations[-1], 3),
                "mean": round(fmean(durations), 3),
                "p95": round(sorted_durations[p95_index], 3),
            },
            "result_count": sum(len(sample.scores) for sample in samples),
            "similarity": {
                "count": len(scores),
                "min": min(scores) if scores else None,
                "max": max(scores) if scores else None,
                "mean": fmean(scores) if scores else None,
                "median": median(scores) if scores else None,
            },
        }


vector_search_metrics = VectorSearchMetrics(settings.VECTOR_SEARCH_METRICS_WINDOW)


def start_vector_search_timer() -> float:
    return perf_counter()


def record_vector_search(
    operation: str,
    started_at: float,
    documents: Iterable[dict[str, Any]],
    score_field: str,
) -> None:
    vector_search_metrics.record(
        operation, perf_counter() - started_at, documents, score_field
    )
