"""Pure monitoring metrics, separated from databases and publication."""

from __future__ import annotations

import numpy as np
import pandas as pd


BIN_EDGES = np.round(np.arange(0.0, 1.0001, 0.05), 2)


def histogram_probabilities(
    similarities: np.ndarray, edges: np.ndarray = BIN_EDGES
) -> np.ndarray:
    values = np.asarray(similarities, dtype=float)
    if values.size == 0:
        raise ValueError("at least one similarity is required")
    counts, _ = np.histogram(values, bins=edges)
    smoothed = counts.astype(float) + 1e-9
    return smoothed / smoothed.sum()


def js_divergence(left: np.ndarray, right: np.ndarray) -> float:
    """Jensen-Shannon divergence in bits."""
    p = np.asarray(left, dtype=float)
    q = np.asarray(right, dtype=float)
    if p.shape != q.shape or p.ndim != 1:
        raise ValueError("probability vectors must have the same one-dimensional shape")
    if not np.isclose(p.sum(), 1.0) or not np.isclose(q.sum(), 1.0):
        raise ValueError("probability vectors must each sum to one")
    midpoint = 0.5 * (p + q)
    left_kl = float(np.sum(np.where(p > 0, p * np.log2(p / midpoint), 0.0)))
    right_kl = float(np.sum(np.where(q > 0, q * np.log2(q / midpoint), 0.0)))
    return 0.5 * left_kl + 0.5 * right_kl


def drift_summary(
    current: np.ndarray,
    baseline: np.ndarray,
    *,
    outlier_threshold: float = 0.35,
    watch_threshold: float = 0.50,
) -> dict[str, float]:
    """Compute descriptive drift signals without deciding whether to publish."""
    now = np.asarray(current, dtype=float)
    before = np.asarray(baseline, dtype=float)
    if now.size == 0 or before.size == 0:
        raise ValueError("current and baseline samples must be non-empty")
    return {
        "mean_similarity": float(now.mean()),
        "baseline_mean_similarity": float(before.mean()),
        "mean_drop": float(before.mean() - now.mean()),
        "js_divergence": js_divergence(
            histogram_probabilities(now),
            histogram_probabilities(before),
        ),
        "outlier_rate": float((now < outlier_threshold).mean()),
        "low_confidence_rate": float((now < watch_threshold).mean()),
    }


def source_concentration(
    documents: pd.DataFrame,
    *,
    group_column: str = "topic_id",
    source_column: str = "source",
    minimum_group_size: int = 5,
) -> pd.DataFrame:
    """Report the largest source share per sufficiently large group."""
    required = {group_column, source_column}
    missing = required.difference(documents.columns)
    if missing:
        raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
    rows = []
    for group, frame in documents.dropna(subset=[source_column]).groupby(group_column):
        if len(frame) < minimum_group_size:
            continue
        rows.append(
            {
                group_column: group,
                "n": len(frame),
                "largest_source_share": float(
                    frame[source_column].value_counts(normalize=True).max()
                ),
            }
        )
    return pd.DataFrame(rows)
