"""Aggregate binary-classifier validation with no document-level data.

The functions in this module operate on a four-cell confusion matrix or on
caller-supplied boolean labels. They deliberately do not load the private TRACE
corpus, model outputs, or annotation records.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from math import sqrt
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ConfusionMatrix:
    """Counts for a binary classifier, with ``True`` as the positive class."""

    true_positive: int
    false_negative: int
    false_positive: int
    true_negative: int

    def __post_init__(self) -> None:
        values = asdict(self).values()
        if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
            raise TypeError("confusion-matrix counts must be integers")
        if any(value < 0 for value in values):
            raise ValueError("confusion-matrix counts must be non-negative")
        if self.total == 0:
            raise ValueError("confusion matrix must contain at least one observation")

    @property
    def total(self) -> int:
        return (
            self.true_positive
            + self.false_negative
            + self.false_positive
            + self.true_negative
        )

    @property
    def actual_positive(self) -> int:
        return self.true_positive + self.false_negative

    @property
    def actual_negative(self) -> int:
        return self.false_positive + self.true_negative

    @property
    def predicted_positive(self) -> int:
        return self.true_positive + self.false_positive

    @property
    def predicted_negative(self) -> int:
        return self.false_negative + self.true_negative


@dataclass(frozen=True)
class BinaryMetrics:
    """Common binary metrics plus the proportion predicted negative."""

    accuracy: float
    precision: float
    recall: float
    f_beta: float
    cohen_kappa: float | None
    predicted_negative_rate: float


def confusion_from_labels(
    reference: Sequence[bool], predicted: Sequence[bool]
) -> ConfusionMatrix:
    """Construct a confusion matrix from equally sized boolean sequences."""
    if len(reference) != len(predicted):
        raise ValueError("reference and predicted labels must have equal length")
    if len(reference) == 0:
        raise ValueError("at least one reference label is required")
    if any(type(value) is not bool for value in (*reference, *predicted)):
        raise TypeError("reference and predicted labels must be booleans")
    pairs = list(zip(reference, predicted, strict=True))
    return ConfusionMatrix(
        true_positive=sum(actual and guess for actual, guess in pairs),
        false_negative=sum(actual and not guess for actual, guess in pairs),
        false_positive=sum(not actual and guess for actual, guess in pairs),
        true_negative=sum(not actual and not guess for actual, guess in pairs),
    )


def _ratio(numerator: int | float, denominator: int | float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def cohen_kappa(matrix: ConfusionMatrix) -> float | None:
    """Return Cohen's kappa, or ``None`` when expected agreement is one."""
    observed = _ratio(
        matrix.true_positive + matrix.true_negative,
        matrix.total,
    )
    expected = (
        matrix.actual_positive * matrix.predicted_positive
        + matrix.actual_negative * matrix.predicted_negative
    ) / matrix.total**2
    if expected == 1.0:
        return None
    return (observed - expected) / (1.0 - expected)


def binary_metrics(matrix: ConfusionMatrix, *, beta: float = 2.0) -> BinaryMetrics:
    """Calculate accuracy, precision, recall, F-beta, kappa and rejection rate.

    Undefined precision or recall is reported as zero. Kappa is reported as
    ``None`` only when its expected-agreement denominator is zero.
    """
    if beta <= 0:
        raise ValueError("beta must be greater than zero")
    precision = _ratio(matrix.true_positive, matrix.predicted_positive)
    recall = _ratio(matrix.true_positive, matrix.actual_positive)
    beta_squared = beta**2
    denominator = beta_squared * precision + recall
    f_beta = (
        (1.0 + beta_squared) * precision * recall / denominator
        if denominator
        else 0.0
    )
    return BinaryMetrics(
        accuracy=_ratio(matrix.true_positive + matrix.true_negative, matrix.total),
        precision=precision,
        recall=recall,
        f_beta=f_beta,
        cohen_kappa=cohen_kappa(matrix),
        predicted_negative_rate=_ratio(matrix.predicted_negative, matrix.total),
    )


def wilson_interval(successes: int, trials: int, *, z: float = 1.96) -> tuple[float, float]:
    """Return a two-sided Wilson score interval for a binomial proportion."""
    if trials <= 0:
        raise ValueError("trials must be greater than zero")
    if successes < 0 or successes > trials:
        raise ValueError("successes must be between zero and trials")
    proportion = successes / trials
    denominator = 1.0 + z**2 / trials
    centre = (proportion + z**2 / (2.0 * trials)) / denominator
    half_width = (
        z
        * sqrt(proportion * (1.0 - proportion) / trials + z**2 / (4.0 * trials**2))
        / denominator
    )
    return max(0.0, centre - half_width), min(1.0, centre + half_width)


def always_positive_baseline(matrix: ConfusionMatrix) -> ConfusionMatrix:
    """Construct the baseline that retains every observation."""
    return ConfusionMatrix(
        true_positive=matrix.actual_positive,
        false_negative=0,
        false_positive=matrix.actual_negative,
        true_negative=0,
    )


def matrix_from_mapping(values: Mapping[str, Any]) -> ConfusionMatrix:
    """Read a confusion matrix from a JSON-compatible mapping."""
    required = {
        "true_positive",
        "false_negative",
        "false_positive",
        "true_negative",
    }
    missing = required.difference(values)
    if missing:
        raise ValueError(f"missing confusion-matrix counts: {', '.join(sorted(missing))}")
    return ConfusionMatrix(**{key: values[key] for key in required})


def verify_result_record(record: Mapping[str, Any], *, tolerance: float = 0.0005) -> BinaryMetrics:
    """Recompute a public aggregate record and reject inconsistent metrics."""
    matrix = matrix_from_mapping(record["confusion_matrix"])
    sample = record.get("sample", {})
    if sample.get("n") != matrix.total:
        raise ValueError("sample size does not match confusion matrix")
    if sample.get("reference_positive") != matrix.actual_positive:
        raise ValueError("reference-positive count does not match confusion matrix")
    if sample.get("reference_negative") != matrix.actual_negative:
        raise ValueError("reference-negative count does not match confusion matrix")

    beta = float(record.get("beta", 2.0))
    metrics = binary_metrics(matrix, beta=beta)
    reported = record.get("metrics", {})
    for key in ("accuracy", "precision", "recall", "f_beta", "cohen_kappa"):
        actual = getattr(metrics, key)
        expected = reported.get(key)
        if actual is None or expected is None:
            if actual != expected:
                raise ValueError(f"reported {key} does not match recomputed value")
        elif abs(actual - float(expected)) > tolerance:
            raise ValueError(f"reported {key} does not match recomputed value")

    baseline = binary_metrics(always_positive_baseline(matrix), beta=beta)
    reported_baseline = record.get("always_positive_baseline", {})
    for key in ("accuracy", "precision", "recall", "f_beta", "predicted_negative_rate"):
        if abs(getattr(baseline, key) - float(reported_baseline.get(key, -1))) > tolerance:
            raise ValueError(
                f"reported always_positive_baseline.{key} does not match recomputed value"
            )

    operating_point = record.get("operating_point", {})
    expected_operating_point = {
        "predicted_negative": matrix.predicted_negative,
        "predicted_negative_rate": matrix.predicted_negative / matrix.total,
        "false_negative_share_of_reference_positive": (
            matrix.false_negative / matrix.actual_positive if matrix.actual_positive else 0.0
        ),
    }
    for key, actual in expected_operating_point.items():
        expected = operating_point.get(key, -1)
        if abs(float(actual) - float(expected)) > tolerance:
            raise ValueError(f"reported operating_point.{key} does not match recomputed value")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="aggregate validation-result JSON")
    args = parser.parse_args()
    record = json.loads(args.result.read_text(encoding="utf-8"))
    metrics = verify_result_record(record)
    matrix = matrix_from_mapping(record["confusion_matrix"])
    baseline = binary_metrics(
        always_positive_baseline(matrix),
        beta=float(record.get("beta", 2.0)),
    )
    print(
        json.dumps(
            {
                "evaluated_model": asdict(metrics),
                "always_positive_baseline": asdict(baseline),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
