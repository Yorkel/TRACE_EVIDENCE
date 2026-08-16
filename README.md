# TRACE_EVIDENCE

> **Public portfolio release — version 2.** This repository contains selected engineering components from TRACE. The research data and live deployment are maintained separately.

[![Public repository checks](https://github.com/Yorkel/TRACE_EVIDENCE/actions/workflows/ci.yml/badge.svg)](https://github.com/Yorkel/TRACE_EVIDENCE/actions/workflows/ci.yml)

TRACE stands for **Testing the Reliability of AI in Consequential Evidence**. It is an engineering and evaluation system for asking whether an AI-assisted finding is reproducible, robust enough for its intended use, and connected to an inspectable evidence trail.

This repository focuses on the technical pipeline: acquisition controls, preprocessing, model training, inference, monitoring, testing and release assurance.

## Architecture

    source acquisition
      → robots and request controls
      → deterministic cleaning and bounded chunking
      → embedding and topic-model training
      → cosine-centroid inference
      → document-level aggregation
      → monitoring and evaluation
      → hash-bound release assurance

## Repository structure

    src/trace_evidence/
        preprocessing.py    deterministic cleaning and chunking
        inference.py        cosine-centroid assignment
        rollup.py           document-level category aggregation
        monitoring.py       drift, novelty and concentration metrics
        robots.py           fail-closed acquisition controls
        release.py          path-safe, hash-bound release manifests

    pipeline/
        training/           embedding and BERTopic training examples
        api/                optional FastAPI inference boundary

    tools/
        build_public_release.py   deny-by-default repository builder
        audit_public_tree.py      privacy, credential and content checks

    tests/                  synthetic and offline regression tests

## Engineering decisions demonstrated here

- **Training and inference use the same preprocessing functions.** This reduces silent train/serve skew.
- **Embedding caches carry data fingerprints.** A cache cannot be mistaken for one produced from different input rows.
- **Model fitting requires an explicit output directory.** The training example refuses to overwrite a non-empty destination.
- **Cosine inference receives versioned centroids and topic identifiers explicitly.** Thresholded observations become visible outliers rather than forced assignments.
- **Outlier chunks remain measurable but do not enter substantive category proportions.**
- **Monitoring calculates descriptive signals without automatically turning them into publication decisions.**
- **Network acquisition fails closed when robots.txt cannot be checked.** Rules are cached and crawl delays are honoured.
- **Release manifests bind reviewed files by SHA-256 and reject absolute paths or path traversal.**
- **The public builder copies only individually allowlisted files and rejects notebooks, data exports, credentials and local paths.**

## Run the verified core

    python -m venv .venv
    source .venv/bin/activate
    pip install -e '.[test]'
    pytest

The current public test suite contains 43 synthetic or offline tests. It does not require the private research corpus or model files.

## Optional components

Install the API example:

    pip install -e '.[api]'
    uvicorn pipeline.api.main:app

Without caller-supplied centroid and scheme files, the API reports itself as unconfigured rather than pretending that a model is available.

Install the training examples:

    pip install -e '.[training]'

Training requires caller-supplied text and embeddings. No source documents, model weights or generated research outputs are distributed in this repository.

## If you are reviewing this as an engineering portfolio

A useful short route through the code is:

1. [Cosine inference](src/trace_evidence/inference.py)
2. [Document roll-up](src/trace_evidence/rollup.py)
3. [Fail-closed acquisition control](src/trace_evidence/robots.py)
4. [Monitoring metrics](src/trace_evidence/monitoring.py)
5. [Release assurance](src/trace_evidence/release.py)
6. [Offline regression tests](tests/)

Together these show the path from controlled input to tested, version-bound evidence.

## Repository boundary

The website, private Git history, research corpus, document-level records, notebooks, model binaries and substantive findings are intentionally not included. This repository demonstrates the engineering system rather than publishing the underlying dataset.

## Licence

MIT.
