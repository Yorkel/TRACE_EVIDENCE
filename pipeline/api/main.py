"""Optional FastAPI boundary for the public cosine-centroid component."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from trace_evidence.inference import classify_embeddings


MAX_ITEMS = 256
MAX_DIMENSIONS = 4096


class VectorItem(BaseModel):
    item_id: str = Field(min_length=1, max_length=200)
    embedding: list[float] = Field(min_length=1, max_length=MAX_DIMENSIONS)


class PredictRequest(BaseModel):
    items: list[VectorItem] = Field(min_length=1, max_length=MAX_ITEMS)
    threshold: float = Field(default=0.35, ge=0.0, le=1.0)


class CentroidBackend:
    def __init__(
        self,
        centroids: np.ndarray,
        topic_ids: np.ndarray,
        scheme: dict[int, dict[str, str]],
    ):
        self.centroids = centroids
        self.topic_ids = topic_ids
        self.scheme = scheme

    @property
    def dimensions(self) -> int:
        return int(self.centroids.shape[1])

    def predict(self, vectors: np.ndarray, threshold: float):
        return classify_embeddings(
            vectors,
            self.centroids,
            self.topic_ids,
            self.scheme,
            threshold=threshold,
        )


def load_backend() -> CentroidBackend | None:
    bundle_path = os.getenv("TRACE_MODEL_BUNDLE")
    scheme_path = os.getenv("TRACE_SCHEME")
    if not bundle_path or not scheme_path:
        return None
    bundle = np.load(Path(bundle_path))
    raw_scheme = json.loads(Path(scheme_path).read_text(encoding="utf-8"))
    scheme = {int(key): value for key, value in raw_scheme.items()}
    return CentroidBackend(
        bundle["centroids"],
        bundle["topic_ids"],
        scheme,
    )


def create_app(backend: CentroidBackend | None = None) -> FastAPI:
    app = FastAPI(title="TRACE Evidence API", version="0.1.0")
    app.state.backend = backend

    @app.get("/health")
    def health():
        active = app.state.backend
        return {
            "status": "ready" if active is not None else "unconfigured",
            "dimensions": active.dimensions if active is not None else None,
        }

    @app.post("/predict")
    def predict(
        request: PredictRequest,
        x_api_key: str | None = Header(default=None),
    ):
        configured_key = os.getenv("TRACE_API_KEY")
        if configured_key and x_api_key != configured_key:
            raise HTTPException(status_code=401, detail="invalid API key")
        active = app.state.backend
        if active is None:
            raise HTTPException(status_code=503, detail="model artefacts not configured")
        vectors = np.asarray([item.embedding for item in request.items], dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[1] != active.dimensions:
            raise HTTPException(status_code=422, detail="embedding dimensions differ")
        frame = active.predict(vectors, request.threshold)
        records = frame.to_dict(orient="records")
        for item, record in zip(request.items, records, strict=True):
            record["item_id"] = item.item_id
        return {"predictions": records, "count": len(records)}

    return app


app = create_app(load_backend())
