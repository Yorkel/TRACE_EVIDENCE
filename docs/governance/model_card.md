# Model Card — TRACE country-specific topic models

## Model and intended use

Version **bertopic_percountry_v1** comprises three BERTopic models: England 75 topics, Scotland 30 and Ireland 33, mapped by the researcher to 20 shared categories. MiniLM (all-MiniLM-L6-v2, 384 dimensions), UMAP and HDBSCAN define the learned topic space; class-based TF-IDF supplies topic terms. Routine inference uses cosine matching to fixed topic centres, with a default outlier threshold of 0.35.

Owner: Louise Yorke, Education Research Programme, UCL Institute of Education. The model supports exploratory comparison, research monitoring and public engagement. It does not estimate official policy, national opinion or individual characteristics. A zero in a fitted category does not prove absence from wider debate.

## Populations and version boundary

Historical training comprised **60,678 passages** (England 46,005; Scotland 6,495; Ireland 8,178). Model selection and tuning retain their historical populations. These must not be confused with the expanded evaluation corpus.

The current evaluation covers publications through **30 September 2026**, captured on 3 November: **10,537 documents, 77,356 passages, 63 sources**; **10,528 categorised documents**. The capture does not reconstruct the database ingestion state on 30 September. See [current results](../results_analysis_bertopic.md) and [aggregate evidence](../../evidence/september_2026.json).

## Evaluation

| Measure | September result | Interpretation |
|---|---|---|
| Median document similarity | 0.6548; IQR 0.5986–0.7015 | Typical fit to the existing framework; not calibrated confidence. |
| Passage outlier rate | 1.788% | Passages below the assignment threshold. |
| Unseen 2026 document median | 0.6437; n=2,976 | Temporal holdout fit, not a topic-accuracy test. |
| BERTopic NPMI, England/Scotland/Ireland | 0.1819 / 0.1929 / 0.2105 | Retrospective topic-word coherence using September reference texts. |
| NMF NPMI, same reference texts | 0.0991 / 0.0966 / 0.1658 | Complementary baseline comparison. |
| BERTopic diversity | 0.951 / 0.937 / 0.964 | Distinct top terms, not assignment accuracy. |

Historical relevance validation used 580 blind-coded documents. Initial recall/precision/kappa were 0.718/0.931/0.590; reviewing disagreements changed 45 of 120 disputed reference labels, producing 0.813/0.946/0.743. This was a reference-set correction, not a model improvement. Rechecking only disagreements limits the reliability interpretation.

A June 2026 judge study using claude-haiku-4-5 on 196 topic-stratified passages found 64.3% category and 58.2% exact-topic agreement. It is diagnostic, not independent ground truth or expert-coded topic accuracy. NMF convergence is interpretive supporting evidence, not formal validation against a prespecified agreement threshold.

## Sensitivity and limits

England supplies 66.15% of categorised documents, Scotland 10.71% and Ireland 23.14%. Within-country shares address unequal totals, not differences in source composition. Schools Week contributes 42.03% of categorised English documents. Dominant-category source removal shifts Scotland’s Poverty & Disadvantage share by 10.128 percentage points when Scottish Government is removed, and shifts an English category by up to 3.312 points when Schools Week is removed.

Alternative mappings change 21.51%, 32.14% and 48.04% of dominant document labels under the stated common tie rule. All 138 identities resolve; 20 stored labels differ only on ties. These are mapping-sensitivity results, not error rates. Their bounds and methods are in the results summary.

Historical seed rebuilds on 7,558 training documents move median shares of 32.8% (England), 36.8% (Ireland) and 42.1% (Scotland) between topic groups. This does not establish national-share or ranking stability. Cross-country category equivalence, a different encoder and expert-coded topic accuracy remain untested.

## Operation and safeguards

TRACE collects and scores weekly; the evaluation snapshot is fixed, while the operating collection continues to grow. Batch inference retains parameters to support comparison. Emerging topics cannot be added automatically. Monthly monitoring examines fit, outliers, low-similarity pools, distribution change and provenance; declining fit prompts review before replacement, not automatic learning.

The baseline mean is 0.6474 with 1.59% outliers. Mean drops of 0.03/0.05 enter review/higher-concern bands; outliers warn at 5%/10%. Pooled January–September passage means range from 0.6227 to 0.6463, above the approximately 0.6174 mean-review threshold. This does not imply every country-month or every signal passed.

Public inference is read-only. Input caps, rate limits and model-version checks have automated endpoint tests. An optional key gate exists but is disabled for the open research interface. Secrets and infrastructure permissions require their own configuration assurance. Versioned images/workflows support a designed rollback route, not a rehearsed production recovery claim; backup/restore verification remains separate work. NMF is a retained comparator, not a claimed live fallback.

## Ethics and provenance

The project records IOE ethics approval REC2360, DPO registration Z6364106/2026/02/116 and a DPIA for secondary public-text processing. Public professional names can remain in source text; no individual profiling or intentional special-category collection is performed. Source URLs, model versions and controlled artefacts support lineage. The public code release excludes raw documents, per-document records and excerpt payloads.
