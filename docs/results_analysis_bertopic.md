# TRACE results — September 2026 evaluation

## Boundary, provenance and measures

These results use publications through **30 September 2026**, captured **3 November 2026**: **10,537 documents, 77,356 passages, 63 sources**. This does not reconstruct database ingestion state on the cutoff date. Model version is **bertopic_percountry_v1**. Weekly operation continues; the fixed evaluation uses the pinned private inputs and independently checked calculation outputs.

The public aggregate registry is [evidence/september_2026.json](../evidence/september_2026.json). It records the source registry hash, private sealed archive hash and snapshot identifier. The public projection excludes raw and document-level data. Its verifier checks aggregate integrity and consistency, not end-to-end recalculation without the private inputs. Historical training, tuning, validation and rebuild studies retain their own populations and dates.

**Fractional document share:** each document has total weight one, split between categories by exact non-outlier passage counts. **Dominant-category share:** each categorised document contributes to one category, with ties resolved by a stated rule. These measures answer different questions and are identified below. No c_v result is claimed.

## Fit and coherence

| Check | Result | What it establishes |
|---|---|---|
| Document median similarity | 0.6548; IQR 0.5986–0.7015 | Fit to the fixed topic centres, not accuracy. |
| Passage outliers | 1.788% | Below-threshold passage rate. |
| Unseen 2026 documents | Median 0.6437; n=2,976 | Temporally held-out fit. |
| Multi-topic documents | 73.138%; mean 3.0458 topics; n=10,528 | A reason to retain within-document mixtures. |

| Country | NMF NPMI | BERTopic NPMI | NMF diversity | BERTopic diversity |
|---|---:|---:|---:|---:|
| England | 0.0991 | 0.1819 | 0.847 | 0.951 |
| Scotland | 0.0966 | 0.1929 | 0.827 | 0.937 |
| Ireland | 0.1658 | 0.2105 | 0.853 | 0.964 |

NPMI uses the same September reference texts for both methods within each country: 1,500 English, all 1,128 Scottish and 1,500 Irish documents, with consistent word/phrase tokenisation. It is a retrospective coherence diagnostic, not evidence available at original model selection. Diversity is distinct top-term coverage. Neither establishes document assignment accuracy.

## Comparative findings

| Country | Leading category | Fractional share |
|---|---|---:|
| England | Governance & Funding | 10.99% |
| Scotland | Poverty & Disadvantage | 18.83% |
| Ireland | Teaching Profession & Workforce | 21.96% |

Poverty & Disadvantage ranks first in Scotland, third in Ireland and fifth in England. Its Scottish fractional share has a **95% percentile bootstrap interval of 17.07%–20.83%**, from **2,000 within-country document resamples of 1,128 Scottish documents**. This describes conditional resampling uncertainty, not missing-source, model-choice or representativeness uncertainty.

Fractional country-category Jensen–Shannon distances (0 identical, 1 maximally different) are England–Scotland **0.4349**, Scotland–Ireland **0.3792**, England–Ireland **0.3537**. Scotland is furthest from the other two on this measure. Shared category names do not establish equivalent meanings.

Under dominant-category counting, country–category chi-square is **1,790.4**, with **38 degrees of freedom**, **n=10,528**, and **Cramér’s V=0.2916**. Restricting to **1,855 government documents** increases V to **0.4286**. This shows association within that restriction, not equivalence or a causal national effect.

## Sources and publisher types

England supplies 66.15%, Scotland 10.71% and Ireland 23.14% of categorised documents. Schools Week supplies 27.80% overall and 42.03% of the English collection. Under dominant-category counting it contributes 61.87% of English School System & Structures and 55.97% of Inspection & Accountability documents.

Dominant-category leave-one-source-out shifts Scotland’s Poverty & Disadvantage share by **10.128 percentage points** when Scottish Government is removed. Removing Schools Week produces a maximum English category shift of **3.312 points**. These are not the fractional headline measure.

Removing English media changes dominant-category Inspection & Accountability from **8.90% to 5.99%**, and Poverty & Disadvantage from **7.90% to 12.96%**. In **10 of 12** country-by-publisher-type cells, removal moves the category mix more than twice as far as removing the same number of documents at random. Publisher composition matters beyond volume alone. These results do not by themselves re-test every headline ranking.

The June coverage investigation retained new sources and the model while qualifying their lack of earlier coverage. Full-period trend comparisons use the more consistent 2023–2025 window. The whole June change was not shown to be an onboarding artefact.

## Mapping sensitivity

All **138 topic identities** resolve, with **zero unmatched documents** in the 10,528-document comparison. Manual and alternative mappings exclude outlier passages, take majority category and break ties using the earliest passage.

| Mapping | Dominant labels changing | Bounds allowing tied alternatives against stored labels |
|---|---:|---:|
| Claude | 21.51% | 20.25%–28.80% |
| GPT | 32.14% | 30.81%–38.16% |
| Embedding based | 48.04% | 46.59%–53.10% |

Twenty stored labels differ from reconstruction only on tied maxima. Point estimates are conditional on the common tie rule; bounds are sensitivity bounds, not confidence intervals or assignment-error rates. These changes do not establish whether national shares or rankings survive an alternative mapping.

## Historical model development and validation

Training used **60,678 passages**. Historical neighbourhood sweeps tested 5/10/15; manual reading favoured 5 over the higher-scoring but over-merged setting. Final minimum cluster sizes are 120/60/70 (England/Scotland/Ireland), min_samples 10, with common encoder, UMAP and label-vectoriser settings. An alternative encoder was not tested. Topic counts reduced from 104/38/53 to 75/30/33 after granularity review.

On **7,558 historical training documents**, random-seed rebuilds moved median shares of **32.8% England, 36.8% Ireland and 42.1% Scotland** between topic groups. Separate one-at-a-time parameter tests left 50.0%/43.1%/29.0% (England/Ireland/Scotland) never moved; halving minimum cluster size moved 24.4%–37.2%. These are distinct tests, not interchangeable movement rates. Repeated scoring against fixed centres is deterministic; rebuilding a model is a different operation. Movement does not establish national-share/ranking stability or that changing input data caused it.

Relevance validation used 580 blind-coded documents. Recall/precision/kappa changed from 0.718/0.931/0.590 to 0.813/0.946/0.743 after reference-label review, not a model change. The June 196-passage judge study gave 64.3% category and 58.2% topic agreement. These are complementary checks; the relevance reference does not validate topics and the model judge is not independent ground truth. NMF supports interpretive convergence rather than formal gold-standard validation.

## Monitoring, corrections and use

The historical monitoring baseline has mean similarity **0.6474** and **1.59%** outliers. Pooled monthly passage means for January–September range **0.6227–0.6463**, above the approximately **0.6174** review threshold. This does not mean every country-month or every metric passed. Mean drops of 0.03/0.05, outliers at 5%/10%, low-similarity pool ratios 2x/3x, per-topic drops 0.05/0.10 and similarity-distribution JS divergence 0.10/0.20 prompt graduated review. This divergence is distinct from country-category distance above.

The shared roll-up was corrected to exclude outliers from substantive category denominators; three regression cases protect it. Claims about “11 of 20 categories comparing cleanly”, “one in six moving on reseeding”, and “88 of 114 pooled topics being England-dominated” were withdrawn after their evidence failed or mixed incompatible tests. See [corrections](corrections.md).

TRACE supports exploratory comparison and examination of how findings depend on evidence and method. It does not demonstrate expert topic accuracy, national representativeness, category equivalence or a continually updating learned model. Separate emerging-topic discovery, expert review and fuller sensitivity displays are development directions. The separately maintained live dashboard is not the numerical authority for this snapshot; publishing source code does not verify deployment availability.
