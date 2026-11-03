# Corrections and scope of the current release

Updated 3 November 2026. The September evaluation fixes a publication-date cutoff, not the ongoing service or collection.

- **Corpus boundary:** June counts of 9,426 documents / 72,548 passages are historical. The current evaluation has 10,537 documents / 77,356 passages, including 10,528 categorised documents. Retained historical experiment outputs keep their original populations.
- **NPMI:** the corrected document-co-occurrence calculation uses common September reference texts within each country. BERTopic NPMI exceeds NMF in all three countries; earlier tie/trailing interpretations are not current. NPMI is retrospective coherence, not assignment accuracy or c_v.
- **Mapping:** current comparison resolves all 138 topic identities with no unmatched documents and explicitly handles 20 stored tie differences. Earlier unmatched-document alternatives are not interchangeable results.
- **Interval:** Scotland’s Poverty & Disadvantage interval is 17.07%–20.83% for an 18.83% fractional document share, using 2,000 resamples of 1,128 documents. A dominant-label interval cannot replace it.
- **Counting:** the shared roll-up excludes outlier passages from substantive shares and retains outlier counts separately; three regression cases protect the correction. Validation continued after publication.
- **Withdrawn claims:** 11/20 categories comparing cleanly failed its shuffled-label comparator; one-in-six seed movement mixed distinct tests; 88/114 England-dominated pooled topics failed its chance comparator.
- **Judge:** the June study has n=196, 64.3% category and 58.2% topic agreement. It is not independent ground truth. Relevance-label recoding corrected the reference set rather than improving the gate.
- **Robustness:** historical composite register survival is not proof of September category-share/rank stability. Rebuild movement, source composition and crosswalk changes are different influences.
- **Operation:** TRACE runs weekly batch inference against fixed topics. NMF is a retained baseline, not a claimed live fallback. Future UCL hosting, recovery rehearsals and full sensitivity displays are separate from deployed-prototype status.

The public aggregate file, model card, datasheet and results summary share this boundary. The live dashboard is maintained separately; this engineering release includes no dashboard assets and does not deploy the website.
