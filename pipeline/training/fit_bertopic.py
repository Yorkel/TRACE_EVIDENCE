"""Fit BERTopic from caller-supplied text, embeddings and optional frozen reduction."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP


class FrozenReduction:
    """Use a saved projection to distinguish refitting from rerunning reduction."""

    def __init__(self, projection: np.ndarray):
        self.projection = projection

    def fit(self, values, labels=None):
        return self

    def fit_transform(self, values, labels=None):
        return self.projection

    def transform(self, values):
        return self.projection


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--frozen-reduction", type=Path)
    parser.add_argument("--fresh-reduction", action="store_true")
    parser.add_argument("--min-cluster-size", type=int, required=True)
    parser.add_argument("--min-samples", type=int, default=10)
    parser.add_argument("--n-neighbors", type=int, default=5)
    args = parser.parse_args()

    if bool(args.frozen_reduction) == bool(args.fresh_reduction):
        parser.error("choose exactly one of --frozen-reduction or --fresh-reduction")
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit("output directory is not empty; refusing to overwrite it")

    frame = pd.read_csv(args.input)
    if args.text_column not in frame:
        raise SystemExit(f"missing text column: {args.text_column}")
    documents = frame[args.text_column].fillna("").astype(str).tolist()
    embeddings = np.load(args.embeddings)["embeddings"]
    if len(documents) != len(embeddings):
        raise SystemExit("document and embedding row counts differ")

    if args.fresh_reduction:
        reduction = UMAP(
            n_neighbors=args.n_neighbors,
            n_components=5,
            min_dist=0.0,
            metric="cosine",
            random_state=42,
            low_memory=True,
        )
    else:
        projection = np.load(args.frozen_reduction)
        if len(projection) != len(embeddings):
            raise SystemExit("frozen reduction and embedding row counts differ")
        reduction = FrozenReduction(projection)

    clusterer = HDBSCAN(
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )
    model = BERTopic(
        umap_model=reduction,
        hdbscan_model=clusterer,
        vectorizer_model=CountVectorizer(
            stop_words="english", min_df=5, ngram_range=(1, 2)
        ),
        ctfidf_model=ClassTfidfTransformer(reduce_frequent_words=True),
        calculate_probabilities=False,
    )
    model.fit_transform(documents, embeddings=embeddings)
    args.output.mkdir(parents=True, exist_ok=True)
    model.save(
        str(args.output),
        serialization="safetensors",
        save_ctfidf=True,
    )
    model.get_topic_info().to_csv(args.output / "topics.csv", index=False)
    print(f"saved model to {args.output}")


if __name__ == "__main__":
    main()
