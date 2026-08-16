"""Document-level aggregation for chunk assignments."""

from __future__ import annotations

import json
from collections import Counter

import pandas as pd


REQUIRED_COLUMNS = {
    "document_id",
    "country",
    "topic_id",
    "topic_name",
    "category",
    "similarity",
}


def rollup_documents(chunks: pd.DataFrame) -> pd.DataFrame:
    """Aggregate chunks while keeping outliers outside substantive proportions."""
    missing = REQUIRED_COLUMNS.difference(chunks.columns)
    if missing:
        raise ValueError(f"missing columns: {', '.join(sorted(missing))}")

    output = []
    for (country, document_id), group in chunks.groupby(
        ["country", "document_id"], sort=False
    ):
        real = group[group["topic_id"] != -1]
        if len(real):
            category_counts = Counter(real["category"])
            proportions = {
                category: round(count / len(real), 4)
                for category, count in category_counts.items()
            }
            dominant_category = max(
                proportions,
                key=lambda category: (proportions[category], category),
            )
            dominant_topic_id = Counter(real["topic_id"]).most_common(1)[0][0]
            dominant_topic_name = real.loc[
                real["topic_id"] == dominant_topic_id, "topic_name"
            ].iloc[0]
            dominant_share = proportions[dominant_category]
        else:
            proportions = {}
            dominant_category = "Outlier"
            dominant_topic_id = -1
            dominant_topic_name = "(outlier)"
            dominant_share = 0.0

        output.append(
            {
                "document_id": document_id,
                "country": country,
                "n_chunks": len(group),
                "n_outlier_chunks": int((group["topic_id"] == -1).sum()),
                "dominant_topic_id": int(dominant_topic_id),
                "dominant_topic_name": dominant_topic_name,
                "dominant_category": dominant_category,
                "dominant_category_share": dominant_share,
                "category_proportions": json.dumps(
                    proportions, sort_keys=True
                ),
                "mean_similarity": round(float(group["similarity"].mean()), 4),
            }
        )
    return pd.DataFrame(output)
