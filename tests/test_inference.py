import numpy as np
import pytest

from trace_evidence.inference import classify_embeddings, cosine_assign


def test_cosine_assignment_is_deterministic():
    centroids = np.array([[1.0, 0.0], [0.0, 1.0]])
    vectors = np.array([[0.9, 0.1], [0.1, 0.9]])
    topics, scores = cosine_assign(vectors, centroids, [10, 20])
    assert topics.tolist() == [10, 20]
    assert np.all(scores > 0.9)


def test_threshold_creates_explicit_outlier():
    topics, _ = cosine_assign(
        np.array([[1.0, 1.0]]),
        np.array([[1.0, 0.0]]),
        [10],
        threshold=0.8,
    )
    assert topics.tolist() == [-1]


def test_classification_maps_topic_metadata():
    frame = classify_embeddings(
        np.array([[1.0, 0.0]]),
        np.array([[1.0, 0.0]]),
        [7],
        {7: {"topic_name": "Synthetic topic", "category": "Synthetic category"}},
    )
    assert frame.iloc[0].to_dict() == {
        "topic_id": 7,
        "topic_name": "Synthetic topic",
        "category": "Synthetic category",
        "similarity": 1.0,
    }


def test_dimension_mismatch_fails():
    with pytest.raises(ValueError, match="dimensions"):
        cosine_assign(np.ones((1, 3)), np.ones((1, 2)), [1])
