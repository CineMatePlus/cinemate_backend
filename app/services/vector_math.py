"""Small vector operations that do not require a platform-specific native runtime."""

from __future__ import annotations

from collections.abc import Sequence


def average_vectors(vectors: Sequence[Sequence[float]]) -> list[float]:
    if not vectors:
        raise ValueError("At least one vector is required.")
    dimensions = len(vectors[0])
    if dimensions == 0:
        raise ValueError("Vectors cannot be empty.")

    totals = [0.0] * dimensions
    for vector in vectors:
        if len(vector) != dimensions:
            raise ValueError("All vectors must have the same dimensions.")
        for index, value in enumerate(vector):
            totals[index] += float(value)

    count = len(vectors)
    return [total / count for total in totals]
