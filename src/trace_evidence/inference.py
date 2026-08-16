"""Deterministic cosine-centroid inference with caller-supplied artefacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd


DEFAULT_THRESHOLD = 0.35


def l2_normalise(values: np.ndarray) -> np.ndarray:
    """L2-normalise rows while keeping zero vectors finite."""
    array = np.asarray(values, dtype=np.float32)
    if array.ndim != 2:
        raise ValueError("expected a two-dimensional array")
    norm = np.linalg.norm(array, axis=1, keepdims=True)
    return array / np.clip(norm, 1e-12, None)


def cosine_assign(
    embeddings: np.ndarray,
    centroids: np.ndarray,
    topic_ids: Sequence[int],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> tuple[np.ndarray, np.ndarray]:
    """Assign each embedding to its nearest centroid or the outlier topic -1."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between zero and one")
    vectors = l2_normalise(embeddings)
    centres = l2_normalise(centroids)
    ids = np.asarray(topic_ids, dtype=int)
    if centres.shape[0] != len(ids):
        raise ValueError("topic_ids and centroids must have equal length")
    if vectors.shape[1] != centres.shape[1]:
        raise ValueError("embedding and centroid dimensions differ")
    similarities = vectors @ centres.T
    best = similarities.argmax(axis=1)
    scores = similarities[np.arange(len(vectors)), best]
    assigned = np.where(scores < threshold, -1, ids[best])
    return assigned.astype(int), scores.astype(float)


def classify_embeddings(
    embeddings: np.ndarray,
    centroids: np.ndarray,
    topic_ids: Sequence[int],
    scheme: Mapping[int, Mapping[str, str]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> pd.DataFrame:
    """Return topic, category and similarity for already-computed embeddings."""
    assigned, scores = cosine_assign(
        embeddings, centroids, topic_ids, threshold=threshold
    )
    rows = []
    for topic_id, score in zip(assigned, scores, strict=True):
        metadata = scheme.get(int(topic_id), {})
        rows.append(
            {
                "topic_id": int(topic_id),
                "topic_name": metadata.get(
                    "topic_name", "(outlier)" if topic_id == -1 else ""
                ),
                "category": metadata.get(
                    "category", "Outlier" if topic_id == -1 else ""
                ),
                "similarity": round(float(score), 4),
            }
        )
    return pd.DataFrame(rows)
