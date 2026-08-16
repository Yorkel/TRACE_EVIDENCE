import json

import pandas as pd
import pytest

from trace_evidence.rollup import rollup_documents


def chunk(document_id, topic_id, category, similarity=0.8):
    return {
        "document_id": document_id,
        "country": "example",
        "topic_id": topic_id,
        "topic_name": f"topic-{topic_id}",
        "category": category,
        "similarity": similarity,
    }


def test_outliers_are_recorded_but_not_in_substantive_denominator():
    frame = pd.DataFrame(
        [
            chunk("A", 1, "Alpha"),
            chunk("A", 1, "Alpha"),
            chunk("A", 2, "Beta"),
            chunk("A", -1, "Outlier", 0.2),
        ]
    )
    result = rollup_documents(frame).iloc[0]
    proportions = json.loads(result.category_proportions)
    assert proportions == {"Alpha": 0.6667, "Beta": 0.3333}
    assert result.n_chunks == 4
    assert result.n_outlier_chunks == 1


def test_all_outlier_document_has_empty_proportions():
    result = rollup_documents(
        pd.DataFrame([chunk("B", -1, "Outlier", 0.1)])
    ).iloc[0]
    assert json.loads(result.category_proportions) == {}
    assert result.dominant_topic_id == -1


def test_missing_columns_fail_explicitly():
    with pytest.raises(ValueError, match="missing columns"):
        rollup_documents(pd.DataFrame({"document_id": ["A"]}))
