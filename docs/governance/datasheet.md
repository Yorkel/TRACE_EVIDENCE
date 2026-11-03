# Datasheet — TRACE public education-policy corpus

## Purpose and ownership

The Education Research Programme at UCL Institute of Education developed TRACE, with UCL Grand Challenges support, to examine public education-policy discourse across England, Scotland and the Republic of Ireland. Louise Yorke designed and maintains the research prototype. The analytical object is the collected documentary record, not representative national opinion.

## September evaluation composition

The publication-date cutoff is **30 September 2026**. Records captured on 3 November contain **10,537 documents, 77,356 passages and 63 sources**, with text available for all documents. This is not an ingestion-state backup taken in September. The first publication date is 2 January 2023. **10,528 documents** have at least one substantive category assignment.

| Country | Categorised documents | Share of categorised corpus |
|---|---:|---:|
| England | 6,964 | 66.15% |
| Scotland | 1,128 | 10.71% |
| Ireland | 2,436 | 23.14% |

Nine documents have no substantive assignment. The historical training set contained 60,678 passages, rather than the expanded September evaluation population. Historical validation and tuning results retain their own populations and dates.

## Collection and preparation

Weekly source-specific adapters collect public government, parliamentary, inspection, research, media, union and other policy material into a canonical Supabase Postgres store. A separate language-model relevance gate applies the documented rubric. URL identifiers prevent duplicate entries; text/content checks flag repeated or changed pages. These controls are not a guarantee of complete source coverage.

Markup, navigation and repeated boilerplate are removed. Sentence-aware passages are approximately 100 words, capped at 40 per document, and represented using 384-dimensional all-MiniLM-L6-v2 embeddings. Topics are assigned within the country model and mapped to 20 categories. Headline shares give each document total weight one, split by its exact non-outlier passage counts. Among categorised documents, 73.138% span multiple topics and the mean is 3.0458 topics.

No synthetic documents were deliberately added. Public sources may contain machine-written text, which is not currently identified. The relevance reference labels were researcher-coded; all 138 topic names and the category crosswalk were manually reviewed. There is no independent expert-coded topic-assignment standard.

## Coverage and bias

Schools Week contributes 2,927 documents, 27.80% of the categorised corpus and 42.03% of categorised English documents. Country and publisher-type composition differ. Within-country normalisation corrects volume imbalance, while source-removal and restricted comparisons examine remaining sensitivities.

A June 2026 investigation identified five newly onboarded sources lacking comparable earlier histories. That historical check concerned 448 records; its old percentage is not a September percentage. Retaining the new material while qualifying coverage and anchoring full-period trend comparisons to 2023–2025 avoids treating onboarding as a change in policy debate. It does not establish that all apparent change is an artefact.

## Personal data, rights and distribution

The collection concerns public professional policy material, not personal records or individual profiling. Public texts can name individuals. No special-category data is intentionally collected. The governance record includes ethics approval, DPO registration and a DPIA; source-specific access and attribution decisions remain relevant even for public material.

The corpus is not redistributed with the public code release. Raw text, per-document identifiers/assignments, source URLs at document level and excerpt payloads remain excluded. Public aggregate results are supplied in evidence/september_2026.json. The operating site and packaged historical dashboard have distinct publication boundaries; neither overrides the pinned evaluation.

## Maintenance and limits

Weekly collection and scoring continue against a consistent topic framework, with monthly monitoring and model-version stamps. NMF remains a comparator after retirement of its scheduled workflows. Retention/deletion/takedown arrangements, maintenance ownership and recovery assurance are part of continued development. Source truth, national representativeness and equivalent category meanings are not established by numerical reproducibility.
