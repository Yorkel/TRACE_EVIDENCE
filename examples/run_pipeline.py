"""Run the public TRACE components on four synthetic documents."""

from __future__ import annotations

import json
from dataclasses import asdict

import numpy as np
import pandas as pd

from trace_evidence.inference import classify_embeddings
from trace_evidence.preprocessing import prepare
from trace_evidence.rollup import rollup_documents
from trace_evidence.validation import binary_metrics, confusion_from_labels


DOCUMENTS = [
    {
        "document_id": "synthetic-1",
        "country": "example",
        "text": "A policy review considers school funding and governance reform.",
        "reference_relevant": True,
    },
    {
        "document_id": "synthetic-2",
        "country": "example",
        "text": "Teachers receive new classroom support and professional development.",
        "reference_relevant": True,
    },
    {
        "document_id": "synthetic-3",
        "country": "example",
        "text": "A catering notice lists the weekly menu.",
        "reference_relevant": False,
    },
    {
        "document_id": "synthetic-4",
        "country": "example",
        "text": "A relevant boundary case uses vocabulary absent from the toy encoder.",
        "reference_relevant": True,
    },
]


def toy_embedding(text: str) -> np.ndarray:
    """Return a deterministic two-feature vector for the offline demonstration."""
    lowered = text.lower()
    governance = sum(word in lowered for word in ("policy", "funding", "governance"))
    teaching = sum(word in lowered for word in ("teacher", "classroom", "support"))
    return np.asarray([governance, teaching], dtype=float)


def main() -> None:
    centroids = np.asarray([[1.0, 0.0], [0.0, 1.0]])
    topic_ids = [10, 20]
    scheme = {
        10: {"topic_name": "Governance", "category": "Systems"},
        20: {"topic_name": "Teaching", "category": "Workforce"},
    }

    chunk_rows = []
    reference = []
    predictions = []
    for document in DOCUMENTS:
        chunks = prepare(str(document["text"]))
        embeddings = np.vstack([toy_embedding(chunk) for chunk in chunks])
        assignments = classify_embeddings(
            embeddings,
            centroids,
            topic_ids,
            scheme,
            threshold=0.60,
        )
        for assignment in assignments.to_dict("records"):
            chunk_rows.append(
                {
                    "document_id": document["document_id"],
                    "country": document["country"],
                    **assignment,
                }
            )
        reference.append(bool(document["reference_relevant"]))
        predictions.append(bool((assignments["topic_id"] != -1).any()))

    rolled_up = rollup_documents(pd.DataFrame(chunk_rows))
    matrix = confusion_from_labels(reference, predictions)
    output = {
        "documents": rolled_up[
            ["document_id", "dominant_category", "n_outlier_chunks"]
        ].to_dict("records"),
        "validation": {
            "confusion_matrix": asdict(matrix),
            "metrics": asdict(binary_metrics(matrix, beta=2)),
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
