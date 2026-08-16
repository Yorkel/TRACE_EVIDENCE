import json
from pathlib import Path

import pytest

from trace_evidence.validation import (
    ConfusionMatrix,
    always_positive_baseline,
    binary_metrics,
    confusion_from_labels,
    verify_result_record,
    wilson_interval,
)


RESULT = Path(__file__).parents[1] / "results" / "relevance_gate_v1.json"


def test_published_counts_reproduce_metrics():
    matrix = ConfusionMatrix(261, 60, 15, 244)
    metrics = binary_metrics(matrix, beta=2)
    assert metrics.accuracy == pytest.approx(0.8706897)
    assert metrics.precision == pytest.approx(0.9456522)
    assert metrics.recall == pytest.approx(0.8130841)
    assert metrics.f_beta == pytest.approx(0.8365385)
    assert metrics.cohen_kappa == pytest.approx(0.7427071)
    assert metrics.predicted_negative_rate == pytest.approx(304 / 580)


def test_always_positive_baseline_is_explicit():
    baseline = always_positive_baseline(ConfusionMatrix(261, 60, 15, 244))
    metrics = binary_metrics(baseline, beta=2)
    assert baseline == ConfusionMatrix(321, 0, 259, 0)
    assert metrics.recall == 1.0
    assert metrics.precision == pytest.approx(321 / 580)
    assert metrics.f_beta == pytest.approx(0.8610515)
    assert metrics.predicted_negative_rate == 0.0


def test_boolean_labels_form_expected_matrix():
    matrix = confusion_from_labels(
        [True, True, False, False],
        [True, False, True, False],
    )
    assert matrix == ConfusionMatrix(1, 1, 1, 1)


def test_wilson_interval_matches_recorded_recall_interval():
    low, high = wilson_interval(261, 321)
    assert low == pytest.approx(0.7668, abs=0.0001)
    assert high == pytest.approx(0.8519, abs=0.0001)


def test_public_result_record_is_self_consistent_and_aggregate_only():
    record = json.loads(RESULT.read_text(encoding="utf-8"))
    metrics = verify_result_record(record)
    assert metrics.cohen_kappa == pytest.approx(0.7427071)
    serialised = json.dumps(record).lower()
    for forbidden in ("item_id", "document_id", "url", "title", "text"):
        assert forbidden not in serialised


def test_invalid_inputs_fail_explicitly():
    with pytest.raises(ValueError, match="non-negative"):
        ConfusionMatrix(-1, 0, 0, 1)
    with pytest.raises(TypeError, match="integers"):
        ConfusionMatrix(1.0, 0, 0, 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at least one observation"):
        ConfusionMatrix(0, 0, 0, 0)
    with pytest.raises(ValueError, match="equal length"):
        confusion_from_labels([True], [])
    with pytest.raises(TypeError, match="booleans"):
        confusion_from_labels([True], [1])
    with pytest.raises(ValueError, match="greater than zero"):
        binary_metrics(ConfusionMatrix(1, 0, 0, 1), beta=0)
    with pytest.raises(ValueError, match="between zero and trials"):
        wilson_interval(2, 1)
    with pytest.raises(ValueError, match="greater than zero"):
        wilson_interval(0, 0)


def test_degenerate_agreement_has_undefined_kappa():
    metrics = binary_metrics(ConfusionMatrix(4, 0, 0, 0))
    assert metrics.cohen_kappa is None


def test_result_verification_rejects_missing_counts_and_sample_mismatch():
    record = json.loads(RESULT.read_text(encoding="utf-8"))
    del record["confusion_matrix"]["false_negative"]
    with pytest.raises(ValueError, match="missing confusion-matrix counts"):
        verify_result_record(record)

    record = json.loads(RESULT.read_text(encoding="utf-8"))
    record["sample"]["n"] = 579
    with pytest.raises(ValueError, match="sample size"):
        verify_result_record(record)

    record = json.loads(RESULT.read_text(encoding="utf-8"))
    record["sample"]["reference_positive"] = 320
    with pytest.raises(ValueError, match="reference-positive"):
        verify_result_record(record)


def test_result_verification_rejects_changed_metric():
    record = json.loads(RESULT.read_text(encoding="utf-8"))
    record["metrics"]["recall"] = 0.99
    with pytest.raises(ValueError, match="reported recall"):
        verify_result_record(record)

    record = json.loads(RESULT.read_text(encoding="utf-8"))
    record["always_positive_baseline"]["f_beta"] = 0.99
    with pytest.raises(ValueError, match="always_positive_baseline.f_beta"):
        verify_result_record(record)

    record = json.loads(RESULT.read_text(encoding="utf-8"))
    record["operating_point"]["predicted_negative"] = 300
    with pytest.raises(ValueError, match="operating_point.predicted_negative"):
        verify_result_record(record)


def test_result_verification_rejects_changed_nullable_kappa():
    record = {
        "sample": {"n": 4, "reference_positive": 4, "reference_negative": 0},
        "confusion_matrix": {
            "true_positive": 4,
            "false_negative": 0,
            "false_positive": 0,
            "true_negative": 0,
        },
        "metrics": {
            "accuracy": 1.0,
            "precision": 1.0,
            "recall": 1.0,
            "f_beta": 1.0,
            "cohen_kappa": 0.0,
        },
    }
    with pytest.raises(ValueError, match="reported cohen_kappa"):
        verify_result_record(record)
