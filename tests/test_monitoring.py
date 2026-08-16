import numpy as np
import pandas as pd
import pytest

from trace_evidence.monitoring import (
    drift_summary,
    histogram_probabilities,
    js_divergence,
    source_concentration,
)


def test_identical_distributions_have_zero_divergence():
    values = histogram_probabilities(np.array([0.2, 0.4, 0.6, 0.8]))
    assert js_divergence(values, values) == pytest.approx(0.0)


def test_drift_summary_keeps_metrics_descriptive():
    result = drift_summary(
        np.array([0.2, 0.3, 0.4]),
        np.array([0.7, 0.8, 0.9]),
    )
    assert result["mean_drop"] == pytest.approx(0.5)
    assert result["outlier_rate"] == pytest.approx(2 / 3)
    assert "status" not in result


def test_source_concentration_uses_sufficient_groups_only():
    frame = pd.DataFrame(
        {
            "topic_id": [1, 1, 1, 1, 2],
            "source": ["a", "a", "a", "b", "z"],
        }
    )
    result = source_concentration(frame, minimum_group_size=3)
    assert result["topic_id"].tolist() == [1]
    assert result.iloc[0].largest_source_share == pytest.approx(0.75)
