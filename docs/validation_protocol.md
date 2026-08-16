# Relevance-gate validation protocol

## Purpose

This evaluation tests a binary relevance gate used before downstream modelling. The
cost of wrongly excluding a relevant document was treated as greater than the cost of
retaining an irrelevant one, so recall was the primary operating concern.

## Reference sample

The evaluation used 580 documents drawn before model evaluation. Sampling was
difficulty-stratified using a fixed, non-model keyword router so that boundary cases
were represented rather than overwhelmed by easy examples. One expert human coded
each document `IN` or `OUT` against frozen rubric version 1.0 without seeing the model
decision.

The public repository does not redistribute the documents, URLs, titles, individual
labels or model responses. It contains only the aggregate four-cell confusion matrix.

## Evaluated system

The recorded result compares the expert labels with one `gpt-4o-mini` relevance gate.
It does not validate the separately planned two-model production ensemble. Three
automated topic-mapping checks used elsewhere in TRACE are also a different evaluation
and are not counted as human coders here.

## Results

| Measure | Result |
|---|---:|
| Documents | 580 |
| True positive | 261 |
| False negative | 60 |
| False positive | 15 |
| True negative | 244 |
| Accuracy | 0.871 |
| Precision | 0.946 |
| Recall | 0.813 |
| Reweighted recall | 0.800 |
| F2 | 0.837 |
| Cohen's kappa | 0.743 |
| Predicted-negative rate | 0.524 |

The model retained relevant material with high precision while predicting `OUT` for
304 of 580 documents. It also missed 60 of the 321 documents the expert marked `IN`.

## Baseline

An always-`IN` rule has recall 1.000, precision 0.553 and F2 0.861 on this sample. Its
F2 is higher than the model's 0.837 because F2 heavily rewards recall and the baseline
never excludes anything. It provides no filtering value, whereas the model predicts
52.4% of the sample `OUT`.

The result is therefore an operating tradeoff, not an unqualified model win. Whether
the reduction in review volume justifies the false exclusions depends on the intended
use and the cost assigned to each error type.

## Reproducibility

The aggregate result is stored in
[`results/relevance_gate_v1.json`](../results/relevance_gate_v1.json). Recompute and
verify its metrics with:

```bash
python -m trace_evidence.validation results/relevance_gate_v1.json
```

The implementation uses the Python standard library and does not require access to the
private corpus or annotation database.

## Limitations

- The reference standard contains one expert coder, so human-human agreement is unknown.
- The planned intra-rater retest is not present in the packaged evidence.
- The result evaluates one model and one frozen rubric at one point in time.
- The difficulty-stratified design requires weighting for a corpus-level estimate;
  reweighted recall is reported, but document-level weights are withheld with the data.
- Performance may change under a different corpus, rubric, model or operating policy.
