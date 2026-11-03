# Robustness and sensitivity — current interpretation

The current evaluation boundary is 30 September 2026, captured 3 November. See [results and methods](results_analysis_bertopic.md) and [aggregate evidence](../evidence/september_2026.json). Historical nb01–nb02 experiments are retained in the private workspace; they are not distributed here or claimed as September reruns.

## What the tests establish

| Test | Population / measure | Result and limit |
|---|---|---|
| Leave one source out | September, dominant document category | Scottish Government removal shifts Scottish Poverty & Disadvantage 10.128pp; Schools Week removal shifts an English category by up to 3.312pp. Different measure from fractional headline shares. |
| Remove a publisher type | September, dominant document category | English Inspection & Accountability 8.90% to 5.99% without media; Poverty & Disadvantage 7.90% to 12.96%. In 10/12 cells, mix shift exceeds twice random-removal shift. |
| Government only | September, dominant category | V rises from 0.2916 (n=10,528) to 0.4286 (n=1,855); collections remain potentially non-equivalent. |
| Alternative category mapping | September, 10,528 categorised documents | 21.51% / 32.14% / 48.04% change dominant label; 138 identities resolved; tie bounds retained. Not an accuracy estimate or ranking-stability test. |
| Seed rebuilds | Historical 7,558 training documents | Median topic-group movement 32.8% England, 36.8% Ireland, 42.1% Scotland. Does not establish national-share stability. |
| Parameter variation | Same historical training split | Never moved: 50.0% England, 43.1% Ireland, 29.0% Scotland. Halving minimum cluster size moves 24.4%–37.2%. Separate from seed medians. |
| NMF comparison | Historical interpretive comparison; retrospective September NPMI | Different representations provide complementary evidence; not independent ground truth. |

## Boundaries on earlier register-survival summaries

The old nb01–nb02 report made claims about coarse, composite “register” survival. It contained a Scotland/Ireland transposition in one headline and stronger generalisations than those tests justify. Those historical composites and their run summaries are different from the September fractional category rankings and document-group movement tests. This release does not promote 11/11 or 9/11 composite survival to evidence that national category shares or rankings are stable under rebuilding.

Deterministic scoring means a fixed model repeats its assignments. It does not make a model correct or robust to alternative construction. Source-removal sensitivity does not identify the cause of every difference, and document movement is not proof of changing data. Shared category names do not establish equivalent meanings. The remaining tests of expert accuracy, formal category equivalence, alternative encoder and aggregate stability are not claimed as completed.
