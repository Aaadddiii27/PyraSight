# PyraSight Final ML Verification Audit

**Status:** PASS_WITH_DOCUMENTED_LIMITATIONS
**Timestamp:** 2026-11-06T18:06:17.757121

## Key results

- Dataset common feature count: 27
- Spatial train-to-held-out minimum distance: 25.0116 km
- Spatial 25 km buffer: True
- Temporal metrics: `{'accuracy': 0.7951028403525955, 'precision': 0.6737297391760234, 'recall': 0.7520604730553524, 'f1': 0.7107434207494123, 'roc_auc': 0.8683715967250791, 'pr_auc': 0.7837892299973914}`
- Spatial metrics: `{'accuracy': 0.7792726779293032, 'precision': 0.6228255845072136, 'recall': 0.6005160684963641, 'f1': 0.6114674023383851, 'roc_auc': 0.8139944192447028, 'pr_auc': 0.6541845133186617}`

## Issues requiring attention

- None detected by automated checks.

## Limitations to document

- Mesogeos dataset covers a historical Mediterranean domain.
- Temporal and spatial results are different evaluation protocols.
- Spatial split is not chronological; time periods may occur in each split.
- The 25 km buffer separates training locations from validation/test locations.
- No 25 km buffer was imposed between validation and test blocks.
- Historical dataset classification metrics do not establish operational forecast skill.
- Dataset negative sampling affects precision, PR-AUC and class prevalence.
- A feature-name audit cannot prove absence of semantic/temporal leakage.

## Interpretation

This is a read-only automated audit. Passing checks do not prove that all features are semantically free of leakage; domain review of the feature definitions and data-generation process is still required.
